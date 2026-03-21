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



