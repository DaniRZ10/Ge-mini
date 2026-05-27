"""
Validadores de claves API de proveedores cloud.
Validación en dos fases: regex de formato y ping HTTP al proveedor.
"""

import re
import httpx
from typing import Tuple


_GEMINI_REGEX = re.compile(r"^AIzaSy[0-9A-Za-z_\-]{33}$")
_GROQ_REGEX = re.compile(r"^gsk_[0-9A-Za-z]{52,}$")
_ANTHROPIC_REGEX = re.compile(r"^sk-ant-[A-Za-z0-9_\-]{80,}$")


async def validate_gemini_key(key: str) -> Tuple[bool, str]:
    if not key:
        return False, "Clave vacía"
    if not _GEMINI_REGEX.match(key):
        return False, "Formato incorrecto (esperado: AIzaSy + 33 chars)"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
            r = await client.get(url)
            if r.status_code == 200:
                return True, ""
            return False, f"HTTP {r.status_code}"
    except httpx.TimeoutException:
        return False, "Timeout al contactar Google"
    except Exception as e:
        return False, f"Error de red: {type(e).__name__}"


async def validate_groq_key(key: str) -> Tuple[bool, str]:
    if not key:
        return False, "Clave vacía"
    if not _GROQ_REGEX.match(key):
        return False, "Formato incorrecto (esperado: gsk_ + 52+ chars)"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {key}"},
            )
            if r.status_code == 200:
                return True, ""
            return False, f"HTTP {r.status_code}"
    except httpx.TimeoutException:
        return False, "Timeout al contactar Groq"
    except Exception as e:
        return False, f"Error de red: {type(e).__name__}"


async def validate_anthropic_key(key: str) -> Tuple[bool, str]:
    if not key:
        return False, "Clave vacía"
    if not _ANTHROPIC_REGEX.match(key):
        return False, "Formato incorrecto (esperado: sk-ant- + 80+ chars)"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(
                "https://api.anthropic.com/v1/models",
                headers={
                    "x-api-key": key,
                    "anthropic-version": "2023-06-01",
                },
            )
            if r.status_code == 200:
                return True, ""
            return False, f"HTTP {r.status_code}"
    except httpx.TimeoutException:
        return False, "Timeout al contactar Anthropic"
    except Exception as e:
        return False, f"Error de red: {type(e).__name__}"
