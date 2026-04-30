import os


def ai_available() -> bool:
    return bool(os.getenv("MAIL_OUTREACH_AI_API_KEY"))


def generate_ai_comment(context: dict) -> str:
    company = context.get("company", "вашей компании")
    category = context.get("category", "вашего направления")
    city = context.get("city", "вашем регионе")
    website = context.get("website", "")
    comment = context.get("comment", "")

    details = []
    if category:
        details.append(f"вы работаете в категории «{category}»")
    if city:
        details.append(f"активны в городе {city}")
    if website:
        details.append(f"посмотрел ваш сайт {website}")
    if comment:
        details.append(f"учел комментарий: {comment}")

    if details:
        joined = "; ".join(details)
        return f"Отдельно отмечу: у компании «{company}» вижу, что {joined}."
    return f"Отдельно отмечу: формат фестиваля может быть полезен компании «{company}» для живого контакта с целевой аудиторией."
