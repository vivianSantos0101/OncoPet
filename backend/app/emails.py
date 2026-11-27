"""Envio de e-mail por SMTP.

Sem SMTP_HOST configurado (desenvolvimento, testes) o e-mail nao sai: o
conteudo, com o link, aparece no log do backend para testar o fluxo.
"""

import logging
import smtplib
import ssl
from email.message import EmailMessage
from html import escape

from . import config

logger = logging.getLogger("oncopet.email")


def send_email(to: str, subject: str, text: str, html: str | None = None) -> bool:
    """Envia o e-mail. Devolve True se saiu; nunca levanta erro (roda em segundo plano)."""
    if not config.SMTP_HOST:
        print(f"[e-mail nao enviado: SMTP nao configurado] Para: {to} | Assunto: {subject}\n{text}", flush=True)
        return False

    msg = EmailMessage()
    msg["From"] = config.SMTP_FROM or config.SMTP_USER
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(text)
    if html:
        msg.add_alternative(html, subtype="html")

    try:
        context = ssl.create_default_context()
        if config.SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT, timeout=15, context=context)
        else:
            server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=15)
        with server:
            if config.SMTP_PORT != 465 and config.SMTP_STARTTLS:
                server.starttls(context=context)
            if config.SMTP_USER:
                server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.send_message(msg)
        print(f"[e-mail] enviado para {to}: {subject}", flush=True)
        return True
    except Exception:  # noqa: BLE001 - qualquer falha de rede/SMTP so vai para o log
        logger.exception("Falha ao enviar e-mail para %s", to)
        print(f"[e-mail] falha ao enviar para {to}", flush=True)
        return False


def password_reset_email(full_name: str, username: str, link: str, minutes: int) -> tuple[str, str, str]:
    """Assunto, texto puro e HTML do e-mail de "esqueci minha senha"."""
    first_name = (full_name or username).split()[0]
    subject = "OncoPet: crie uma nova senha"
    text = (
        f"Olá, {first_name}!\n\n"
        f"Recebemos um pedido para criar uma nova senha da sua conta no OncoPet (usuário: {username}).\n\n"
        f"Para criar a nova senha, abra o link abaixo. Ele vale por {minutes} minutos e só pode ser usado uma vez:\n"
        f"{link}\n\n"
        "Se você não pediu, é só ignorar este e-mail: sua senha continua a mesma.\n\n"
        "Equipe OncoPet"
    )
    n, u, lk = escape(first_name), escape(username), escape(link, quote=True)
    html = f"""<!doctype html>
<html lang="pt-BR"><body style="margin:0;padding:24px;background:#f3faf7;font-family:Arial,Helvetica,sans-serif;color:#22343c;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center">
<table role="presentation" width="520" cellpadding="0" cellspacing="0" style="max-width:520px;background:#ffffff;border-radius:20px;padding:36px;">
<tr><td style="font-size:26px;font-weight:bold;color:#0b8a64;padding-bottom:20px;">OncoPet</td></tr>
<tr><td style="font-size:16px;line-height:1.6;">
<p style="margin:0 0 14px;">Olá, <b>{n}</b>!</p>
<p style="margin:0 0 14px;">Recebemos um pedido para criar uma nova senha da sua conta no OncoPet (usuário: <b>{u}</b>).</p>
<p style="margin:0 0 24px;">O botão abaixo vale por <b>{minutes} minutos</b> e só pode ser usado uma vez.</p>
</td></tr>
<tr><td align="center" style="padding-bottom:24px;">
<a href="{lk}" style="display:inline-block;background:#12b886;color:#ffffff;text-decoration:none;font-weight:bold;font-size:16px;padding:14px 32px;border-radius:999px;">Criar nova senha</a>
</td></tr>
<tr><td style="font-size:13px;line-height:1.5;color:#5f7179;">
<p style="margin:0 0 10px;">Se o botão não funcionar, copie este endereço no navegador:<br><span style="word-break:break-all;">{lk}</span></p>
<p style="margin:0;">Se você não pediu, é só ignorar este e-mail: sua senha continua a mesma.</p>
</td></tr>
</table></td></tr></table></body></html>"""
    return subject, text, html
