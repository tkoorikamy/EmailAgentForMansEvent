from app.core.template_engine import generate_email
from app.core.ai_personalizer import generate_ai_comment


def test_generate_email():
    subject, body = generate_email({"company": "Ромашка", "contact_name": "Иван", "ai_comment": "AI-блок"}, "Привет {{ company }}", "Здравствуйте {{ contact_name }} {{ ai_comment }}")
    assert subject == "Привет Ромашка"
    assert body == "Здравствуйте Иван AI-блок"


def test_ai_comment_contains_company():
    comment = generate_ai_comment({"company": "Ромашка", "category": "спорт"})
    assert "Ромашка" in comment
