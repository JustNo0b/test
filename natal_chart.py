from kerykeion import AstrologicalSubjectFactory, NatalAspects

factory = AstrologicalSubjectFactory()

subject = factory.from_birth_data(
    name="Egor",
    year=1996,
    month=10,
    day=24,
    hour=1,
    minute=32,
    city="Moscow",
    nation="RU",
    zodiac_type="Tropical",
    houses_system_identifier="P",
    online=True,
    suppress_geonames_warning=True,
)

sign_ru = {
    "Ari": "Овен", "Tau": "Телец", "Gem": "Близнецы", "Can": "Рак",
    "Leo": "Лев", "Vir": "Дева", "Lib": "Весы", "Sco": "Скорпион",
    "Sag": "Стрелец", "Cap": "Козерог", "Aqu": "Водолей", "Pis": "Рыбы",
}

planet_ru = {
    "Sun": "Солнце", "Moon": "Луна", "Mercury": "Меркурий", "Venus": "Венера",
    "Mars": "Марс", "Jupiter": "Юпитер", "Saturn": "Сатурн",
    "Uranus": "Уран", "Neptune": "Нептун", "Pluto": "Плутон",
    "Chiron": "Хирон", "Mean_Lilith": "Лилит (ср.)", "True_North_Lunar_Node": "Сев. Узел (ист.)",
    "True_South_Lunar_Node": "Юж. Узел (ист.)", "Mean_North_Lunar_Node": "Сев. Узел (ср.)",
    "Mean_South_Lunar_Node": "Юж. Узел (ср.)",
}

house_ru = {
    "First_House": "I дом", "Second_House": "II дом", "Third_House": "III дом",
    "Fourth_House": "IV дом (IC)", "Fifth_House": "V дом", "Sixth_House": "VI дом",
    "Seventh_House": "VII дом (DSC)", "Eighth_House": "VIII дом", "Ninth_House": "IX дом",
    "Tenth_House": "X дом (MC)", "Eleventh_House": "XI дом", "Twelfth_House": "XII дом",
}

aspect_ru = {
    "conjunction": "Соединение", "opposition": "Оппозиция", "trine": "Трин",
    "square": "Квадрат", "sextile": "Секстиль", "quincunx": "Квинконс",
    "semi-sextile": "Полусекстиль", "semi-square": "Полуквадрат",
    "sesquiquadrate": "Полутораквадрат", "quintile": "Квинтиль",
    "bi-quintile": "Биквинтиль",
}

element_ru = {"Fire": "Огонь", "Earth": "Земля", "Air": "Воздух", "Water": "Вода"}
quality_ru = {"Cardinal": "Кардинальный", "Fixed": "Фиксированный", "Mutable": "Мутабельный"}

planet_attrs = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]
extra_attrs = ["chiron", "mean_lilith", "true_north_lunar_node", "true_south_lunar_node"]
house_attrs = [
    "first_house", "second_house", "third_house", "fourth_house",
    "fifth_house", "sixth_house", "seventh_house", "eighth_house",
    "ninth_house", "tenth_house", "eleventh_house", "twelfth_house",
]

planets = [getattr(subject, a) for a in planet_attrs]
extras = [getattr(subject, a) for a in extra_attrs if getattr(subject, a, None) is not None]
houses = [getattr(subject, a) for a in house_attrs]

output = []

output.append("=" * 70)
output.append("НАТАЛЬНАЯ КАРТА — ЕГОР")
output.append("=" * 70)
output.append(f"Дата рождения:  24 октября 1996 года, 01:32")
output.append(f"Место рождения: Москва, Россия ({subject.lat:.4f}° с.ш., {subject.lng:.4f}° в.д.)")
output.append(f"Часовой пояс:   {subject.tz_str}")
output.append(f"UTC время:      {subject.iso_formatted_utc_datetime}")
output.append(f"Система домов:  Плацидус")
output.append(f"Зодиак:         Тропический")
output.append(f"Юлианский день: {subject.julian_day:.6f}")
output.append("")

output.append("=" * 70)
output.append("ПОЛОЖЕНИЯ ПЛАНЕТ")
output.append("=" * 70)
output.append(f"{'Планета':20s} {'Знак':12s} {'Градус':>8s}  {'Дом':16s} {'Retro':>5s}")
output.append("-" * 70)
for p in planets + extras:
    name = planet_ru.get(p.name, p.name)
    sign = sign_ru.get(p.sign, p.sign)
    house = house_ru.get(p.house, p.house) if p.house else ""
    retro = "(R)" if p.retrograde else ""
    output.append(f"  {name:18s} {sign:12s} {p.position:7.2f}°  {house:16s} {retro:>5s}")

output.append("")
output.append("=" * 70)
output.append("ДОМА (КУСПИДЫ)")
output.append("=" * 70)
for h in houses:
    name = house_ru.get(h.name, h.name)
    sign = sign_ru.get(h.sign, h.sign)
    output.append(f"  {name:18s} {sign:12s} {h.position:7.2f}°")

output.append("")
output.append("=" * 70)
output.append("АСПЕКТЫ")
output.append("=" * 70)
aspects_obj = NatalAspects(subject)
for asp in aspects_obj.relevant_aspects:
    p1 = planet_ru.get(asp["p1_name"], asp["p1_name"])
    p2 = planet_ru.get(asp["p2_name"], asp["p2_name"])
    asp_name = aspect_ru.get(asp["aspect"], asp["aspect"])
    output.append(f"  {p1:18s} {asp_name:18s} {p2:18s} (орбис {asp['orbit']:+.2f}°)")

output.append("")
output.append("=" * 70)
output.append("РАСПРЕДЕЛЕНИЕ ПО СТИХИЯМ (10 планет)")
output.append("=" * 70)
elements = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
for p in planets:
    if p.element in elements:
        elements[p.element] += 1
for el, cnt in elements.items():
    bar = "█" * cnt
    output.append(f"  {element_ru[el]:10s} ({cnt}): {bar}")

output.append("")
output.append("=" * 70)
output.append("РАСПРЕДЕЛЕНИЕ ПО КРЕСТАМ (10 планет)")
output.append("=" * 70)
qualities = {"Cardinal": 0, "Fixed": 0, "Mutable": 0}
for p in planets:
    if p.quality in qualities:
        qualities[p.quality] += 1
for q, cnt in qualities.items():
    bar = "█" * cnt
    output.append(f"  {quality_ru[q]:18s} ({cnt}): {bar}")

report_text = "\n".join(output)
print(report_text)

with open("/workspace/natal_chart_egor.txt", "w", encoding="utf-8") as f:
    f.write(report_text)
