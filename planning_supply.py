import db_worker


def plan_supply_from_wb_items(
    items: list[dict],
    max_supply: int,
    target_days: int = 14,
    integer_days: bool = True,
    in_transit_by_warehouse_vendor: dict[str, dict[str, int]] | None = None,
    excluded_warehouses_for_supply: set[str] | None = None,
) -> dict:
    """
    items: массив элементов вида
    {
        "nmID": ...,
        "vendor": ...,
        "data": {
            "offices": [
                {
                    "officeName": "...",
                    "metrics": {
                        "ordersCount": ...,
                        "stockCount": ...
                    }
                },
                ...
            ]
        }
    }

    in_transit_by_warehouse_vendor:
    {
        "Коледино": {"MP1": 128, "MP2": 20},
        "Казань": {"MP1": 99},
        "Электросталь": {}
    }

    excluded_warehouses_for_supply:
        склады, которые нельзя выбирать как склад поставки
        например {"Остальные", "Маркетплейс"}

    Возвращает:
    {
        "target_days": ...,
        "best_warehouse": ...,
        "total_shipment": ...,
        "shipment_plan_by_nmid": {...},
        "shipment_plan_by_vendor": {...},
        "warehouse_scores": {...},
        "items": [...]
    }
    """

    if in_transit_by_warehouse_vendor is None:
        in_transit_by_warehouse_vendor = {}

    if excluded_warehouses_for_supply is None:
        excluded_warehouses_for_supply = {"Остальные", "Маркетплейс"}

    # --------------------------------------------------
    # 1. Парсим входные данные
    # --------------------------------------------------
    parsed_items = []
    warehouses_set = set(in_transit_by_warehouse_vendor.keys())

    for item in items:
        nm_id = item.get("nmID")
        vendor = item.get("vendor")
        offices = item.get("data", {}).get("offices", [])

        office_data = {}

        for office in offices:
            office_name = office.get("officeName")
            metrics = office.get("metrics", {})

            if not office_name:
                continue

            orders_count = float(metrics.get("ordersCount", 0) or 0)
            stock_count = float(metrics.get("stockCount", 0) or 0)

            office_data[office_name] = {
                "orders_14d": orders_count,
                "stock": stock_count,
            }
            warehouses_set.add(office_name)

        parsed_items.append({
            "nmID": nm_id,
            "vendor": vendor,
            "offices": office_data,
        })

    warehouses = sorted(warehouses_set)

    # --------------------------------------------------
    # 2. Нормализуем данные по складам и учитываем товары в пути
    # --------------------------------------------------
    for item in parsed_items:
        total_daily_sales = 0.0
        total_stock = 0.0
        total_in_transit = 0.0

        vendor = item["vendor"]

        for wh in warehouses:
            office_info = item["offices"].get(wh, {"orders_14d": 0.0, "stock": 0.0})

            daily_sales = office_info["orders_14d"] / 14.0
            stock = float(office_info["stock"])
            in_transit_qty = float(in_transit_by_warehouse_vendor.get(wh, {}).get(vendor, 0) or 0)

            office_info["daily_sales"] = daily_sales
            office_info["in_transit_qty"] = in_transit_qty
            office_info["effective_stock"] = stock + in_transit_qty

            item["offices"][wh] = office_info

            total_daily_sales += daily_sales
            total_stock += stock
            total_in_transit += in_transit_qty

        item["network_daily_sales"] = total_daily_sales
        item["network_stock"] = total_stock
        item["network_in_transit"] = total_in_transit
        item["effective_network_stock"] = total_stock + total_in_transit

    # --------------------------------------------------
    # 3. Функции расчёта потребности по сети
    # need_i(T) = max(0, D_i * T - effective_network_stock_i)
    # --------------------------------------------------
    def need_for_item(item: dict, days: float) -> float:
        return max(0.0, item["network_daily_sales"] * days - item["effective_network_stock"])

    def total_need(days: float) -> float:
        return sum(need_for_item(item, days) for item in parsed_items)

    # --------------------------------------------------
    # 4. Ищем максимальный достижимый горизонт
    # --------------------------------------------------
    if total_need(target_days) <= max_supply:
        best_days = float(target_days)
    else:
        if integer_days:
            left = 0
            right = int(target_days)

            while left < right:
                mid = (left + right + 1) // 2
                if total_need(mid) <= max_supply:
                    left = mid
                else:
                    right = mid - 1

            best_days = float(left)
        else:
            left = 0.0
            right = float(target_days)

            for _ in range(60):
                mid = (left + right) / 2.0
                if total_need(mid) <= max_supply:
                    left = mid
                else:
                    right = mid

            best_days = left

    # --------------------------------------------------
    # 5. Считаем план поставки по каждому товару
    # --------------------------------------------------
    shipment_plan_by_nmid = {}
    shipment_plan_by_vendor = {}

    for item in parsed_items:
        qty = need_for_item(item, best_days)
        qty = int(round(qty))

        if qty < 0:
            qty = 0

        shipment_plan_by_nmid[item["nmID"]] = qty
        shipment_plan_by_vendor[item["vendor"]] = qty

    total_shipment = sum(shipment_plan_by_nmid.values())

    # если после округления немного вылезли за лимит — подрезаем
    if total_shipment > max_supply:
        overflow = total_shipment - max_supply

        sortable = sorted(
            parsed_items,
            key=lambda x: shipment_plan_by_nmid[x["nmID"]],
            reverse=True
        )

        idx = 0
        while overflow > 0 and sortable:
            item = sortable[idx % len(sortable)]
            nm_id = item["nmID"]
            vendor = item["vendor"]

            if shipment_plan_by_nmid[nm_id] > 0:
                shipment_plan_by_nmid[nm_id] -= 1
                shipment_plan_by_vendor[vendor] -= 1
                overflow -= 1

            idx += 1

    # --------------------------------------------------
    # 6. Считаем score для каждого склада
    # local_deficit = max(0, daily_sales * T - effective_stock_on_warehouse)
    # --------------------------------------------------
    warehouse_scores = {}
    local_deficits = {}

    candidate_warehouses = [
        wh for wh in warehouses
        if wh not in excluded_warehouses_for_supply
    ]

    for wh in candidate_warehouses:
        score = 0.0
        local_deficits[wh] = {}

        for item in parsed_items:
            office_info = item["offices"][wh]

            daily_sales_wh = office_info["daily_sales"]
            effective_stock_wh = office_info["effective_stock"]

            local_deficit = max(0.0, daily_sales_wh * best_days - effective_stock_wh)
            useful_qty = min(float(shipment_plan_by_nmid[item["nmID"]]), local_deficit)

            local_deficits[wh][item["nmID"]] = local_deficit
            score += useful_qty

        warehouse_scores[wh] = score

    # --------------------------------------------------
    # 7. Выбираем лучший склад
    # --------------------------------------------------
    best_warehouse = None
    if warehouse_scores:
        best_warehouse = max(warehouse_scores, key=warehouse_scores.get)

    # --------------------------------------------------
    # 8. Доп. информация по товарам
    # --------------------------------------------------
    items_result = []

    for item in parsed_items:
        item_offices = {}

        for wh in warehouses:
            office_info = item["offices"][wh]
            item_offices[wh] = {
                "orders_14d": office_info["orders_14d"],
                "daily_sales": office_info["daily_sales"],
                "stock": office_info["stock"],
                "in_transit_qty": office_info["in_transit_qty"],
                "effective_stock": office_info["effective_stock"],
            }

        items_result.append({
            "nmID": item["nmID"],
            "vendor": item["vendor"],
            "network_daily_sales": item["network_daily_sales"],
            "network_stock": item["network_stock"],
            "network_in_transit": item["network_in_transit"],
            "effective_network_stock": item["effective_network_stock"],
            "shipment_qty": shipment_plan_by_nmid[item["nmID"]],
            "offices": item_offices,
        })

    return {
        "target_days": best_days,
        "best_warehouse": best_warehouse,
        "total_shipment": sum(shipment_plan_by_nmid.values()),
        "shipment_plan_by_nmid": shipment_plan_by_nmid,
        "shipment_plan_by_vendor": shipment_plan_by_vendor,
        "warehouse_scores": warehouse_scores,
        "local_deficits": local_deficits,
        "items": items_result,
    }


import math
from typing import Any, Optional


def calc_supply_for_warehouse(
    items: list[dict[str, Any]],
    warehouse_id: int,
    target_days: int | float,
    in_transit_by_warehouse_vendor: Optional[dict[str, dict[str, int | float]]] = None,
    sales_period_days: int | float = 14,
    include_zero_sales: bool = True,
    include_zero_shipment: bool = True,
) -> dict[str, Any]:
    """
    Считает, сколько каждого товара нужно отгрузить на конкретный склад.

    :param items: список товаров из WB-аналитики
    :param warehouse_id: officeID склада, например 206348 для Тулы
    :param target_days: на сколько дней должен хватить товар
    :param in_transit_by_warehouse_vendor: {'Тула': {'DB1': 24, ...}}
    :param sales_period_days: за сколько дней ordersCount, по умолчанию 14
    :param include_zero_sales: включать ли товары без продаж
    :param include_zero_shipment: включать ли товары, которым не нужна отгрузка
    """

    if target_days <= 0:
        raise ValueError("target_days должен быть больше 0")

    if sales_period_days <= 0:
        raise ValueError("sales_period_days должен быть больше 0")

    in_transit_by_warehouse_vendor = in_transit_by_warehouse_vendor or {}

    warehouse_name = _find_warehouse_name_by_id(items, warehouse_id)

    transit_for_warehouse = in_transit_by_warehouse_vendor.get(warehouse_name, {})

    result_items = []

    totals = {
        "stockCount": 0,
        "inTransitCount": 0,
        "effectiveStockCount": 0,
        "ordersCount": 0,
        "dailySales": 0,
        "targetStockCount": 0,
        "needToShipCount": 0,
    }

    for item in items:
        nm_id = item.get("nmID")
        vendor = str(item.get("vendor", "")).strip()
        timestamp = item.get("timestamp")

        office = _find_office_in_item(item, warehouse_id)

        if office is None:
            metrics = {}
            office_found = False
            region_name = None
            office_name = warehouse_name
        else:
            metrics = office.get("metrics") or {}
            office_found = True
            region_name = office.get("regionName")
            office_name = office.get("officeName")

        stock_count = _to_number(metrics.get("stockCount"))
        orders_count = max(0, _to_number(metrics.get("ordersCount")))
        orders_sum = max(0, _to_number(metrics.get("ordersSum")))
        buyout_count = max(0, _to_number(metrics.get("buyoutCount")))
        buyout_sum = max(0, _to_number(metrics.get("buyoutSum")))
        buyout_percent = max(0, _to_number(metrics.get("buyoutPercent")))

        daily_sales = orders_count / sales_period_days

        in_transit_count, matched_transit_keys = _get_in_transit_qty(
            vendor=vendor,
            transit_for_warehouse=transit_for_warehouse,
        )

        effective_stock = stock_count + in_transit_count

        if daily_sales > 0:
            target_stock = math.ceil(daily_sales * target_days)
            need_to_ship = max(0, target_stock - effective_stock)

            days_with_current_stock = stock_count / daily_sales
            days_with_in_transit = effective_stock / daily_sales
            days_after_shipment = (effective_stock + need_to_ship) / daily_sales
        else:
            target_stock = 0
            need_to_ship = 0

            days_with_current_stock = None
            days_with_in_transit = None
            days_after_shipment = None

        if not include_zero_sales and orders_count == 0:
            continue

        if not include_zero_shipment and need_to_ship == 0:
            continue

        item_result = {
            "nmID": nm_id,
            "vendor": vendor,
            "timestamp": timestamp,

            "warehouse": {
                "officeID": warehouse_id,
                "officeName": office_name,
                "regionName": region_name,
                "foundInProductOffices": office_found,
            },

            "sales": {
                "ordersCount": orders_count,
                "ordersSum": orders_sum,
                "salesPeriodDays": sales_period_days,
                "dailySales": round(daily_sales, 4),

                "buyoutCount": buyout_count,
                "buyoutSum": buyout_sum,
                "buyoutPercent": buyout_percent,
            },

            "stock": {
                "stockCount": stock_count,
                "inTransitCount": in_transit_count,
                "matchedTransitVendorKeys": matched_transit_keys,
                "effectiveStockCount": effective_stock,
            },

            "planning": {
                "targetDays": target_days,
                "targetStockCount": target_stock,
                "needToShipCount": int(need_to_ship),

                "daysWithCurrentStock": _round_or_none(days_with_current_stock),
                "daysWithInTransit": _round_or_none(days_with_in_transit),
                "daysAfterShipment": _round_or_none(days_after_shipment),

                "shortageBeforeShipment": int(max(0, target_stock - effective_stock)),
                "surplusBeforeShipment": int(max(0, effective_stock - target_stock)),
            },
        }

        result_items.append(item_result)

        totals["stockCount"] += stock_count
        totals["inTransitCount"] += in_transit_count
        totals["effectiveStockCount"] += effective_stock
        totals["ordersCount"] += orders_count
        totals["dailySales"] += daily_sales
        totals["targetStockCount"] += target_stock
        totals["needToShipCount"] += need_to_ship

    result_items.sort(
        key=lambda x: (
            x["planning"]["needToShipCount"],
            x["sales"]["dailySales"],
            x["sales"]["ordersCount"],
        ),
        reverse=True,
    )

    total_daily_sales = totals["dailySales"]

    if total_daily_sales > 0:
        total_days_with_current_stock = totals["stockCount"] / total_daily_sales
        total_days_with_in_transit = totals["effectiveStockCount"] / total_daily_sales
        total_days_after_shipment = (
            totals["effectiveStockCount"] + totals["needToShipCount"]
        ) / total_daily_sales
    else:
        total_days_with_current_stock = None
        total_days_with_in_transit = None
        total_days_after_shipment = None

    return {
        "warehouse": {
            "officeID": warehouse_id,
            "officeName": warehouse_name,
        },
        "params": {
            "targetDays": target_days,
            "salesPeriodDays": sales_period_days,
            "inTransitIsCountedAsArrived": True,
        },
        "summary": {
            "itemsCount": len(result_items),

            "totalStockCount": int(totals["stockCount"]),
            "totalInTransitCount": int(totals["inTransitCount"]),
            "totalEffectiveStockCount": int(totals["effectiveStockCount"]),

            "totalOrdersCount": int(totals["ordersCount"]),
            "totalDailySales": round(total_daily_sales, 4),

            "totalTargetStockCount": int(totals["targetStockCount"]),
            "totalNeedToShipCount": int(totals["needToShipCount"]),

            "totalDaysWithCurrentStock": _round_or_none(total_days_with_current_stock),
            "totalDaysWithInTransit": _round_or_none(total_days_with_in_transit),
            "totalDaysAfterShipment": _round_or_none(total_days_after_shipment),
        },
        "items": result_items,
    }


def _find_warehouse_name_by_id(
    items: list[dict[str, Any]],
    warehouse_id: int,
) -> str:
    for item in items:
        for office in item.get("data", {}).get("offices", []):
            if office.get("officeID") == warehouse_id:
                return office.get("officeName")

    raise ValueError(f"Склад с officeID={warehouse_id} не найден в данных товаров")


def _find_office_in_item(
    item: dict[str, Any],
    warehouse_id: int,
) -> Optional[dict[str, Any]]:
    for office in item.get("data", {}).get("offices", []):
        if office.get("officeID") == warehouse_id:
            return office

    return None


def _get_in_transit_qty(
    vendor: str,
    transit_for_warehouse: dict[str, int | float],
) -> tuple[int, list[str]]:
    """
    Ищет товар в поставках в пути.

    Поддерживает:
    - точное совпадение: KFB1
    - составные ключи через /: DB5/KFB1

    Это нужно из-за таких записей:
    {'Казань': {'DB5/KFB1': 3}}
    """

    total = 0
    matched_keys = []

    vendor_parts = _split_vendor_code(vendor)

    for transit_vendor_key, qty in transit_for_warehouse.items():
        transit_vendor_key = str(transit_vendor_key).strip()
        transit_parts = _split_vendor_code(transit_vendor_key)

        matched = bool(vendor_parts & transit_parts)

        if matched:
            total += _to_number(qty)
            matched_keys.append(transit_vendor_key)

    return int(total), matched_keys


def _split_vendor_code(value: str) -> set[str]:
    return {
        part.strip()
        for part in str(value).split("/")
        if part.strip()
    }


def _to_number(value: Any) -> float:
    if value is None:
        return 0

    try:
        return float(value)
    except (TypeError, ValueError):
        return 0


def _round_or_none(value: Optional[float], ndigits: int = 2) -> Optional[float]:
    if value is None:
        return None

    return round(value, ndigits)



if __name__ == "__main__":
    import db_worker
    import json
    import wb_api_helper
    import wb_supply_excel_export
    import wb_supply_barcode_export
    import wb_export_report_extended

    r = db_worker.get_all_nmid_data()
    import config_io
    WB_TOKEN = config_io.get_value('WB_TOKEN')

    result = plan_supply_from_wb_items(r, 2000, 28, in_transit_by_warehouse_vendor=wb_api_helper.get_fbw_in_transit_by_warehouse_and_vendor_code(WB_TOKEN))

    wb_export_report_extended.export_supply_plan_to_excel(result, 'отчет2.xlsx', 28, 2000, 0.7622)
    wb_supply_excel_export.export_supply_plan_to_excel(result, 'отчет.xlsx', 28, 2000)
    wb_supply_barcode_export.export_supply_barcodes_to_excel(result, 'генерация.xlsx', barcode_by_nmid=wb_api_helper.nm_id_to_barcode(WB_TOKEN))

    with open('test.json', 'w') as f:
        f.write(json.dumps(result))



