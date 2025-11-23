from datetime import date, timedelta
import re

# ile elementów generować przy automatycznych powtórzeniach
AUTO_REPEAT_DAILY = 7
AUTO_REPEAT_WEEKLY = 7

# opcje powtarzania
REPEAT_OPTIONS = [
    "Brak", "Codziennie", "Co tydzień", "Co weekend",
    "Co poniedziałek", "Co wtorek", "Co środa",
    "Co czwartek", "Co piątek", "Co sobota", "Co niedziela",
]

WEEKDAY_MAP = {
    "Co poniedziałek": 0,
    "Co wtorek": 1,
    "Co środa": 2,
    "Co czwartek": 3,
    "Co piątek": 4,
    "Co sobota": 5,
    "Co niedziela": 6,
}


def fmt_ddmm(d: date) -> str:
    """Zwraca datę w formacie dd.mm."""
    return f"{d.day:02d}.{d.month:02d}"


def meta_to_ddmm_date(meta: str | None) -> date | None:
    """
    Zamienia meta typu 'dd.mm' na obiekt date (z bieżącym rokiem).
    Jeśli meta jest puste albo błędne – zwraca None.
    """
    if not meta:
        return None
    m = str(meta).strip().replace(" ", "")
    match = re.fullmatch(r"(\d{1,2})\.(\d{1,2})", m)
    if not match:
        return None
    d_str, mo_str = match.groups()
    try:
        return date(date.today().year, int(mo_str), int(d_str))
    except ValueError:
        return None


def next_weekday(start_from: date, weekday: int) -> date:
    """
    Zwraca pierwszą datę (po start_from), która wypada w dany dzień tygodnia.
    weekday: 0 = pon, 6 = niedziela.
    """
    d = start_from + timedelta(days=1)
    days_ahead = (weekday - d.weekday()) % 7
    return d + timedelta(days=days_ahead)


def generate_repeats(pattern: str, start_from: date) -> list[date]:
    """
    Generuje listę dat powtórzeń licząc od start_from (bez samego start_from).
    Wykorzystuje stałe AUTO_REPEAT_DAILY, AUTO_REPEAT_WEEKLY oraz WEEKDAY_MAP.
    """
    if pattern == "Brak":
        return []

    dates: list[date] = []

    if pattern == "Codziennie":
        start = start_from + timedelta(days=1)
        for i in range(AUTO_REPEAT_DAILY):
            dates.append(start + timedelta(days=i))

    elif pattern == "Co tydzień":
        start = start_from + timedelta(days=7)
        for i in range(AUTO_REPEAT_WEEKLY):
            dates.append(start + timedelta(days=7 * i))

    elif pattern == "Co weekend":
        # 5 = sobota
        first_sat = next_weekday(start_from, 5)
        for i in range(AUTO_REPEAT_WEEKLY):
            dates.append(first_sat + timedelta(days=7 * i))

    elif pattern in WEEKDAY_MAP:
        wd = WEEKDAY_MAP[pattern]
        first = next_weekday(start_from, wd)
        for i in range(AUTO_REPEAT_WEEKLY):
            dates.append(first + timedelta(days=7 * i))

    return dates
