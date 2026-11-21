"""Sinh bộ SVG tự tạo cho game vào chonoi/web/assets/ (Ticket-04, "Tự do sáng tạo": đồ họa).

    python3 tools/gen_assets.py

Mọi hình vẽ bằng code, không dùng tài sản ngoài nên không vướng bản quyền (ghi ở CREDITS.md: "tự tạo").
Quy ước hướng: cá, Cá Sấu và Út Sen quay về +x (phải); client xoay theo `heading_deg`. Hình chỉ dùng ở client,
headless không đọc nên không ảnh hưởng tick, sự kiện, tiền, uy tín hay snapshot.
"""

import os
import xml.etree.ElementTree as ET

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chonoi", "web", "assets")


def svg(w, h, body, defs=""):
    d = f"<defs>{defs}</defs>" if defs else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
            f"{d}{body}</svg>\n")


# ---------------------------------------------------------------- nhân vật
CHECK = ('<pattern id="r" width="8" height="8" patternUnits="userSpaceOnUse">'
         '<rect width="8" height="8" fill="#f4efe2"/><rect width="4" height="4" fill="#22252c"/>'
         '<rect x="4" y="4" width="4" height="4" fill="#22252c"/></pattern>')

USEN = svg(64, 64, """
<rect x="3" y="27" width="20" height="24" rx="8" fill="#a87b45" stroke="#6f4b25" stroke-width="2"/>
<path d="M6 33h14M6 39h14M6 45h14M10 28v22M16 28v22" stroke="#6f4b25" stroke-width="1.2" fill="none"/>
<path d="M22 40c0-9 20-10 22 0l2 16H20z" fill="#2d3a5a"/>
<path d="M30 38l8 6-8 6" stroke="#3f5080" stroke-width="2" fill="none"/>
<circle cx="38" cy="22" r="12" fill="#e8b48a"/>
<path d="M25 20c3-12 22-12 25 0v3H25z" fill="url(#r)" stroke="#22252c" stroke-width="1.2"/>
<path d="M26 19l-9-4 3 7z" fill="url(#r)" stroke="#22252c" stroke-width="1"/>
<circle cx="45" cy="24" r="5.5" fill="#8ed8e8" stroke="#3d3d3d" stroke-width="2"/>
<path d="M27 24h12" stroke="#3d3d3d" stroke-width="2"/>
<circle cx="46.5" cy="23" r="1.4" fill="#fff"/>
<path d="M42 31q4 2 8 0" stroke="#b5654a" stroke-width="1.6" fill="none" stroke-linecap="round"/>
<ellipse cx="46" cy="46" rx="6" ry="3" fill="#e8b48a" transform="rotate(20 46 46)"/>
""", CHECK)

# ---------------------------------------------------------------- cá (32 cao, quay +x)
CA_LINH = svg(64, 32, """
<path d="M10 16L1 8l3 8-3 8z" fill="#9fbccb"/>
<path d="M10 16C18 7 42 6 56 16 42 26 18 25 10 16z" fill="#cfe3ee" stroke="#8aa9ba" stroke-width="1.2"/>
<path d="M14 18C26 22 42 22 54 17 42 25 22 25 14 18z" fill="#eef6fa"/>
<path d="M26 9l6-5 6 6" fill="#9fbccb"/>
<circle cx="49" cy="14" r="2.6" fill="#fff"/><circle cx="49.6" cy="14" r="1.4" fill="#1c2b36"/>
<path d="M42 11q3 5 0 10" stroke="#8aa9ba" stroke-width="1.2" fill="none"/>
""")

CA_LOC = svg(64, 32, """
<path d="M9 16C3 12 2 8 1 6l2 10-2 10c1-2 2-6 8-10z" fill="#4c5a28"/>
<path d="M9 16C16 9 44 8 59 14c2 3 2 4 0 7C44 25 16 24 9 16z" fill="#6b7f3a" stroke="#3f4d1f" stroke-width="1.2"/>
<path d="M13 11C27 6 44 7 53 11 43 9 25 9 13 11z" fill="#3f4d1f"/>
<path d="M12 19C26 24 44 24 58 20 44 22 26 21 12 19z" fill="#d8d49a"/>
<path d="M18 14l6 4M28 13l6 5M38 13l6 5" stroke="#46571f" stroke-width="2" fill="none"/>
<circle cx="52" cy="14" r="2.6" fill="#f1e6a0"/><circle cx="52.6" cy="14" r="1.4" fill="#222"/>
<path d="M58 17q2 1 3 0" stroke="#3f4d1f" stroke-width="1.2" fill="none"/>
""")

CA_KEO = svg(64, 32, """
<path d="M9 17L1 9l2 8-2 8z" fill="#b97a3d"/>
<path d="M8 17C14 8 40 5 56 13c3 4 1 8-6 9C36 26 14 26 8 17z" fill="#c98a4b" stroke="#7d5126" stroke-width="1.2"/>
<path d="M18 9l5-5 5 5M30 8l5-5 6 6" fill="#e0a864" stroke="#7d5126" stroke-width="1"/>
<circle cx="20" cy="16" r="1.5" fill="#7d5126"/><circle cx="28" cy="18" r="1.5" fill="#7d5126"/>
<circle cx="36" cy="16" r="1.5" fill="#7d5126"/>
<circle cx="50" cy="13" r="3" fill="#fff"/><circle cx="50.8" cy="13" r="1.6" fill="#222"/>
<path d="M56 18q-2 2-5 1" stroke="#7d5126" stroke-width="1.2" fill="none"/>
""")

CA_SAU = svg(128, 48, """
<path d="M10 26C2 22 0 18 0 14c6 4 12 6 18 8z" fill="#2e4522"/>
<path d="M6 28C16 12 62 12 92 20l30 2c4 1 5 5 2 7L92 33C62 41 16 40 6 28z" fill="#3d5a2e" stroke="#243619" stroke-width="1.5"/>
<path d="M20 17l4-6 4 6M34 14l4-6 4 6M48 13l4-6 4 6M62 14l4-6 4 6M76 16l4-6 4 6" fill="#2e4522"/>
<path d="M12 30C40 38 80 36 120 28 90 36 40 34 12 30z" fill="#a3b57a"/>
<path d="M96 27l3 4 3-4 3 4 3-4 3 4 3-4 3 4" fill="#fff" stroke="#e8e0cf" stroke-width=".8"/>
<circle cx="103" cy="19" r="4.5" fill="#f6d54a" stroke="#243619" stroke-width="1.2"/>
<ellipse cx="103.6" cy="19" rx="1.2" ry="3.6" fill="#1b1b1b"/>
<ellipse cx="26" cy="42" rx="6" ry="3" fill="#243619" transform="rotate(-25 26 42)"/>
<ellipse cx="44" cy="43" rx="6" ry="3" fill="#243619" transform="rotate(-25 44 43)"/>
<ellipse cx="62" cy="43" rx="6" ry="3" fill="#243619" transform="rotate(-25 62 43)"/>
<ellipse cx="80" cy="42" rx="6" ry="3" fill="#243619" transform="rotate(-25 80 42)"/>
<ellipse cx="98" cy="40" rx="6" ry="3" fill="#243619" transform="rotate(-25 98 40)"/>
""")

# ---------------------------------------------------------------- cây nổi trên mặt nước (40 cao)
BONG_DIEN_DIEN = svg(64, 40, """
<ellipse cx="32" cy="34" rx="26" ry="5" fill="#4f8a3c"/>
<path d="M10 34c4-6 10-6 14 0M40 34c4-6 10-6 14 0" fill="#6aa84f"/>
<path d="M32 34V18M24 34l-4-14M40 34l4-14" stroke="#3d7a2e" stroke-width="2" fill="none"/>
<g fill="#f6c915" stroke="#c9970a" stroke-width="1">
<circle cx="32" cy="14" r="6"/><circle cx="19" cy="17" r="5"/><circle cx="45" cy="17" r="5"/>
<circle cx="26" cy="8" r="4"/><circle cx="38" cy="8" r="4"/></g>
<g fill="#fff3a0"><circle cx="32" cy="14" r="2"/><circle cx="19" cy="17" r="1.6"/><circle cx="45" cy="17" r="1.6"/></g>
""")

BONG_SUNG = svg(64, 40, """
<path d="M4 34a28 6 0 1 0 56 0 28 6 0 1 0-56 0z" fill="#3f8f4d"/>
<path d="M32 34L50 29" stroke="#2f6f3a" stroke-width="2"/>
<path d="M32 30C22 28 18 18 22 10c6 2 10 8 10 20z" fill="#f48fb1" stroke="#c2577f" stroke-width="1"/>
<path d="M32 30C42 28 46 18 42 10c-6 2-10 8-10 20z" fill="#f48fb1" stroke="#c2577f" stroke-width="1"/>
<path d="M32 30C27 26 26 14 32 4c6 10 5 22 0 26z" fill="#f8bbd0" stroke="#c2577f" stroke-width="1"/>
<circle cx="32" cy="24" r="3" fill="#ffe082"/>
""")

KEO_NEO = svg(64, 40, """
<ellipse cx="32" cy="34" rx="26" ry="5" fill="#8fbf6a"/>
<g stroke="#5e9b45" stroke-width="2" fill="none" stroke-linecap="round">
<path d="M32 34V12M32 26l-10-8M32 26l10-8M32 20l-8-8M32 20l8-8M22 34l-8-12M42 34l8-12"/></g>
<g fill="#7fc455"><ellipse cx="32" cy="10" rx="4" ry="6"/><ellipse cx="22" cy="17" rx="4" ry="2.5"/>
<ellipse cx="42" cy="17" rx="4" ry="2.5"/><ellipse cx="14" cy="21" rx="3.5" ry="2.2"/>
<ellipse cx="50" cy="21" rx="3.5" ry="2.2"/></g>
<ellipse cx="32" cy="35" rx="10" ry="4" fill="#f4efd6" stroke="#cdbf8c" stroke-width="1"/>
""")

# ---------------------------------------------------------------- bến
DOCK = svg(96, 80, """
<path d="M6 34L48 6l42 28z" fill="#b9503a" stroke="#7d2f20" stroke-width="2"/>
<path d="M20 28l28-18M34 30l22-14M52 30l24-14" stroke="#8f3a29" stroke-width="1.5" fill="none"/>
<rect x="20" y="34" width="56" height="22" fill="#d9b382" stroke="#9a7747" stroke-width="2"/>
<rect x="43" y="38" width="12" height="18" fill="#5a3d22"/>
<rect x="26" y="40" width="10" height="9" fill="#8ed8e8" stroke="#5a3d22" stroke-width="1.5"/>
<rect x="62" y="40" width="10" height="9" fill="#8ed8e8" stroke="#5a3d22" stroke-width="1.5"/>
<rect x="4" y="56" width="88" height="10" fill="#8d6e4b" stroke="#5a3d22" stroke-width="2"/>
<path d="M18 56v10M34 56v10M50 56v10M66 56v10M82 56v10" stroke="#5a3d22" stroke-width="1.5"/>
<path d="M10 66v12M48 66v12M86 66v12" stroke="#5a3d22" stroke-width="4" stroke-linecap="round"/>
<circle cx="48" cy="24" r="4" fill="#ffe082" stroke="#7d2f20" stroke-width="1"/>
""")

# ---------------------------------------------------------------- nhà bè (nhìn từ trên xuống)
STOVE = svg(64, 64, """
<rect x="6" y="38" width="52" height="20" rx="4" fill="#7b6a5a" stroke="#4a3f35" stroke-width="2"/>
<path d="M10 46h44M24 38v20M40 38v20" stroke="#4a3f35" stroke-width="1.5"/>
<path d="M14 30h36l-3 10H17z" fill="#3a3f47" stroke="#1f2227" stroke-width="2"/>
<ellipse cx="32" cy="30" rx="18" ry="5" fill="#4b525c" stroke="#1f2227" stroke-width="2"/>
<path d="M26 22q-3-4 0-8M34 22q-3-4 0-9M42 22q-3-4 0-8" stroke="#dfe7ee" stroke-width="2" fill="none" opacity=".7" stroke-linecap="round"/>
<rect x="22" y="42" width="20" height="14" rx="3" fill="#2a211b"/>
<path d="M32 55c-8-3-8-9-3-13 0 4 3 5 5 2 3 3 4 8-2 11z" fill="#ff8a30"/>
<path d="M32 55c-4-2-4-5-1-7 0 2 3 2 3 5z" fill="#ffd54f"/>
""")

TABLE = svg(64, 64, """
<circle cx="32" cy="32" r="28" fill="#6b4423" stroke="#3f2713" stroke-width="2"/>
<circle cx="32" cy="32" r="22" fill="#a8713a"/>
<path d="M32 10v44M10 32h44" stroke="#8a5a2e" stroke-width="1.2"/>
<circle cx="32" cy="32" r="5" fill="#f4efe2" stroke="#c9b98f" stroke-width="1.5"/>
<path d="M20 22l8 4M44 40l-8-4" stroke="#e8dfc4" stroke-width="2" stroke-linecap="round"/>
""")

CUSTOMER = svg(64, 64, """
<ellipse cx="10" cy="40" rx="7" ry="13" fill="#6a4c8c"/><ellipse cx="54" cy="40" rx="7" ry="13" fill="#6a4c8c"/>
<circle cx="32" cy="30" r="25" fill="#ecd9a0" stroke="#b79a54" stroke-width="2"/>
<path d="M32 30L32 5M32 30l22-12M32 30l22 12M32 30L32 55M32 30L10 42M32 30L10 18"
 stroke="#c9ae6c" stroke-width="1.5"/>
<circle cx="32" cy="30" r="4" fill="#b79a54"/>
""")


# ---------------------------------------------------------------- món ăn (48x48)
def dish(body):
    return svg(48, 48, '<circle cx="24" cy="24" r="22" fill="#fff8e6" stroke="#d8c79c" stroke-width="2"/>' + body)


DISHES = {
    "ca_loc_nuong_trui": dish("""
<path d="M6 30c8 9 28 9 36 0z" fill="#3f8f4d"/>
<path d="M8 24C14 15 32 14 42 22c0 3-1 4-2 6-10 5-24 4-32-4z" fill="#8a6b3a" stroke="#5a431f" stroke-width="1.5"/>
<path d="M16 21l4 6M24 20l4 7M32 21l3 6" stroke="#3f2d12" stroke-width="2"/>
<circle cx="37" cy="22" r="1.8" fill="#fff"/>"""),
    "goi_bong_sung": dish("""
<path d="M7 24h34c0 10-8 17-17 17S7 34 7 24z" fill="#e8c9a0" stroke="#b78f5a" stroke-width="1.5"/>
<g fill="#f48fb1" stroke="#c2577f" stroke-width=".8"><path d="M14 22c2-8 8-8 10 0z"/><path d="M24 22c2-9 9-9 11 0z"/>
<path d="M19 22c1-6 6-6 7 0z"/></g>
<path d="M12 24c3-3 5-3 8 0M26 24c3-3 6-3 9 0" stroke="#6aa84f" stroke-width="2.5" fill="none"/>"""),
    "lau_ca_linh_dien_dien": dish("""
<path d="M6 22h36l-3 14c-1 4-6 6-15 6s-14-2-15-6z" fill="#7a5c3a" stroke="#4a3520" stroke-width="1.5"/>
<ellipse cx="24" cy="22" rx="18" ry="5" fill="#e8b24a"/>
<circle cx="16" cy="21" r="3" fill="#f6c915"/><circle cx="24" cy="23" r="3" fill="#f6c915"/><circle cx="31" cy="21" r="3" fill="#f6c915"/>
<path d="M12 22l5-2-1 4zM28 24l5-1-2 3z" fill="#cfe3ee"/>
<path d="M18 14q-2-4 0-6M26 14q-2-4 0-6" stroke="#cfd8dc" stroke-width="2" fill="none" stroke-linecap="round"/>"""),
    "canh_chua_ca_loc": dish("""
<path d="M6 22h36c0 11-8 18-18 18S6 33 6 22z" fill="#e8c9a0" stroke="#b78f5a" stroke-width="1.5"/>
<ellipse cx="24" cy="22" rx="18" ry="4.5" fill="#e0693a"/>
<path d="M12 22c4-5 10-5 14 0-4 4-10 4-14 0z" fill="#e8dcb0" stroke="#a8914f" stroke-width="1"/>
<circle cx="31" cy="21" r="3" fill="#f6c915"/><circle cx="35" cy="23" r="2.4" fill="#f6c915"/>
<path d="M20 22l4-3" stroke="#5aa044" stroke-width="2"/>"""),
    "ca_keo_nuong": dish("""
<ellipse cx="24" cy="26" rx="19" ry="10" fill="#3f8f4d"/>
<path d="M7 25c5-8 24-9 34 0-3 6-9 9-17 9s-14-3-17-9z" fill="#c98a4b" stroke="#7d5126" stroke-width="1.5"/>
<path d="M14 23l3 5M21 22l3 6M29 22l3 6" stroke="#7d5126" stroke-width="2"/>
<g fill="#d8341f"><ellipse cx="18" cy="30" rx="3" ry="1.4"/><ellipse cx="30" cy="29" rx="3" ry="1.4"/></g>
<circle cx="36" cy="24" r="1.8" fill="#fff"/>"""),
    "lau_mam": dish("""
<path d="M5 20h38l-3 17c-1 5-7 7-16 7s-15-2-16-7z" fill="#5a4636" stroke="#2e231a" stroke-width="1.5"/>
<ellipse cx="24" cy="20" rx="19" ry="5.5" fill="#9a6a3a"/>
<path d="M10 20l5-3M20 21l6-4M30 20l5-3" stroke="#6aa84f" stroke-width="3" stroke-linecap="round"/>
<circle cx="15" cy="21" r="2.6" fill="#f6c915"/><circle cx="33" cy="21" r="2.6" fill="#f6c915"/>
<path d="M22 21l5-2-1 4z" fill="#cfe3ee"/><path d="M13 13q-2-4 0-6M22 13q-2-4 0-7M31 13q-2-4 0-6"
 stroke="#cfd8dc" stroke-width="2" fill="none" stroke-linecap="round"/>"""),
}

# ---------------------------------------------------------------- biểu tượng cảnh báo (48x48; HUD thêm chữ)
WARN_MONSTER = svg(48, 48, """
<path d="M24 3L46 42H2z" fill="#7b3fbf" stroke="#3d1f66" stroke-width="3" stroke-linejoin="round"/>
<path d="M24 16v14" stroke="#fff" stroke-width="5" stroke-linecap="round"/><circle cx="24" cy="36" r="3" fill="#fff"/>
<path d="M12 40l3-4 3 4 3-4 3 4 3-4 3 4 3-4 3 4" fill="#fff" opacity=".9"/>""")

WARN_OXYGEN = svg(48, 48, """
<circle cx="24" cy="24" r="21" fill="#e53935" stroke="#7f1d1b" stroke-width="3"/>
<g fill="none" stroke="#fff" stroke-width="2.5"><circle cx="15" cy="13" r="3"/><circle cx="23" cy="8" r="2"/><circle cx="32" cy="12" r="3.5"/></g>
<path d="M24 20v11" stroke="#fff" stroke-width="5" stroke-linecap="round"/><circle cx="24" cy="38" r="3" fill="#fff"/>""")

WARN_ANGRY = svg(48, 48, """
<circle cx="24" cy="24" r="21" fill="#ff9800" stroke="#8a4b00" stroke-width="3"/>
<path d="M10 14l11 6M38 14l-11 6" stroke="#3a1f00" stroke-width="4" stroke-linecap="round"/>
<circle cx="16" cy="24" r="3" fill="#3a1f00"/><circle cx="32" cy="24" r="3" fill="#3a1f00"/>
<path d="M14 36q10-8 20 0" stroke="#3a1f00" stroke-width="4" fill="none" stroke-linecap="round"/>""")

ASSETS = {
    "usen": USEN, "ca_linh": CA_LINH, "ca_loc": CA_LOC, "ca_keo": CA_KEO, "ca_sau": CA_SAU,
    "bong_dien_dien": BONG_DIEN_DIEN, "bong_sung": BONG_SUNG, "keo_neo": KEO_NEO,
    "dock": DOCK, "stove": STOVE, "table": TABLE, "customer": CUSTOMER,
    "warn_monster": WARN_MONSTER, "warn_oxygen": WARN_OXYGEN, "warn_angry": WARN_ANGRY,
    **{f"dish_{k}": v for k, v in DISHES.items()},
}


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    for name, text in sorted(ASSETS.items()):
        ET.fromstring(text)  # hỏng XML thì dừng ngay
        with open(os.path.join(OUT, name + ".svg"), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    print(f"đã ghi {len(ASSETS)} SVG vào {os.path.relpath(OUT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
