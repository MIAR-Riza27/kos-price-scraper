"""Utility functions for handling dynamic selectors"""

def detect_room_card_selector(page, selectors, timeout=10000):
    """Deteksi selector room card yang tepat untuk region ini."""
    # Coba selector utama dulu
    try:
        page.wait_for_selector(
            selectors["room_card_primary"],
            timeout=timeout,
            state="attached"
        )
        print("    * [Selector: Primary]")
        return selectors["room_card_primary"]
    except Exception:
        pass
    
    # Jika gagal, coba fallback
    try:
        page.wait_for_selector(
            selectors["room_card_fallback"],
            timeout=timeout,
            state="attached"
        )
        print("    * [Selector: Fallback]")
        return selectors["room_card_fallback"]
    except Exception:
        pass
    
    # Semua gagal
    return None

def get_room_cards(page, selector):
    """Ambil semua room cards menggunakan selector yang sudah terdeteksi."""
    return page.locator(selector).all()