import json
from datetime import datetime, timedelta, date


def calculate_sales_ratio_from_json_by_calendar_days(
    json_path: str,
    days_forward: int,
    base_date: str | date | datetime,
    prefer_future_year: bool = True,
) -> dict:
    """
    Считает коэффициент:
        (средние продажи за days_forward дней вперед) /
        (средние продажи за 14 дней до)

    Но поиск идет НЕ по точной дате, а по календарному дню MM-DD.
    Если нужного года нет, берется тот же MM-DD из другого года.

    Логика выбора даты для одного календарного дня:
    1) если есть точная дата target_date -> берем ее
    2) иначе, если prefer_future_year=True:
       - берем ближайший год >= target.year
       - если таких нет, берем ближайший год < target.year
    3) если prefer_future_year=False:
       - наоборот, сначала ближайший год <= target.year,
         потом ближайший > target.year

    Пример:
        target day = 2025-03-20
        в файле есть только 2026-03-20
        -> будет взято 2026-03-20
    """

    if days_forward <= 0:
        raise ValueError("days_forward должен быть > 0")

    if isinstance(base_date, datetime):
        base_date_obj = base_date.date()
    elif isinstance(base_date, date):
        base_date_obj = base_date
    elif isinstance(base_date, str):
        base_date_obj = datetime.strptime(base_date, "%Y-%m-%d").date()
    else:
        raise TypeError("base_date должен быть str, date или datetime")

    with open(json_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    if not isinstance(raw_data, dict):
        raise ValueError("JSON должен быть объектом формата {дата: продажи}")

    # exact_sales: {date_obj: value}
    exact_sales = {}

    # by_month_day: {"03-20": [(date_obj, value), ...]}
    by_month_day = {}

    for k, v in raw_data.items():
        try:
            d = datetime.strptime(str(k), "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"Некорректная дата в JSON: {k}")

        try:
            val = float(v)
        except (TypeError, ValueError):
            raise ValueError(f"Некорректное значение продаж для даты {k}: {v}")

        exact_sales[d] = val

        md = d.strftime("%m-%d")
        by_month_day.setdefault(md, []).append((d, val))

    for md in by_month_day:
        by_month_day[md].sort(key=lambda x: x[0])

    def resolve_calendar_day(target_date: date) -> tuple[date, float]:
        """
        Возвращает реальную дату из JSON и значение продаж
        для календарного дня target_date.month-day.
        """
        if target_date in exact_sales:
            return target_date, exact_sales[target_date]

        md = target_date.strftime("%m-%d")
        candidates = by_month_day.get(md)

        if not candidates:
            raise ValueError(
                f"В JSON вообще нет данных для календарного дня {md}"
            )

        target_year = target_date.year

        future_candidates = [(d, val) for d, val in candidates if d.year >= target_year]
        past_candidates = [(d, val) for d, val in candidates if d.year < target_year]

        if prefer_future_year:
            if future_candidates:
                return min(future_candidates, key=lambda x: x[0].year - target_year)
            return max(past_candidates, key=lambda x: x[0].year)
        else:
            if past_candidates:
                return max(past_candidates, key=lambda x: x[0].year)
            return min(future_candidates, key=lambda x: x[0].year - target_year)

    # 14 дней до base_date: [base_date - 14 ; base_date - 1]
    past_requested = [
        base_date_obj - timedelta(days=i)
        for i in range(14, 0, -1)
    ]

    # days_forward дней после base_date: [base_date + 1 ; base_date + days_forward]
    future_requested = [
        base_date_obj + timedelta(days=i)
        for i in range(1, days_forward + 1)
    ]

    past_resolved = [resolve_calendar_day(d) for d in past_requested]
    future_resolved = [resolve_calendar_day(d) for d in future_requested]

    past_values = [val for _, val in past_resolved]
    future_values = [val for _, val in future_resolved]

    past_avg = sum(past_values) / 14
    future_avg = sum(future_values) / days_forward

    ratio = None if past_avg == 0 else future_avg / past_avg

    return {
        "base_date": base_date_obj.isoformat(),
        "past_14_days": {
            "requested_calendar_days": [d.isoformat() for d in past_requested],
            "used_dates": [d.isoformat() for d, _ in past_resolved],
            "values": past_values,
            "average_per_day": past_avg,
        },
        "future_period": {
            "days_forward": days_forward,
            "requested_calendar_days": [d.isoformat() for d in future_requested],
            "used_dates": [d.isoformat() for d, _ in future_resolved],
            "values": future_values,
            "average_per_day": future_avg,
        },
        "ratio_future_to_past": ratio,
    }


if __name__ == "__main__":
    print(calculate_sales_ratio_from_json_by_calendar_days('report_coof.json', 28, '2025-12-01'))