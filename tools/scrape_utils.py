import os
import json
import time
import random
from datetime import datetime
import glob


def detect_bot_block(room_data):
    """Deteksi apakah halaman di-block karena bot detection."""
    critical_fields = ["nama_kos", "area", "alamat", "harga"]
    empty_count = sum(1 for field in critical_fields if not room_data.get(field, "").strip())
    
    if empty_count >= 3:
        return True
    
    if not room_data.get("nama_kos", "").strip() and room_data.get("url", ""):
        return True
        
    return False


def handle_bot_detection(new_page, retry_count=0, max_retry=3):
    """Handle bot detection dengan strategi anti-detection."""
    if retry_count >= max_retry:
        return False
    
    # Shorter, cleaner output
    delay = random.uniform(3, 8) + (retry_count * 2)
    
    # Strategy 1: Longer random delays
    time.sleep(delay)
    
    # Strategy 2: Human-like scrolling patterns
    scroll_patterns = [
        [0, 0.2, 0.5, 0.8, 1.0, 0.3, 0.7, 0],
        [0, 0.3, 0.1, 0.6, 0.9, 0.4, 0.8, 0],
        [0, 0.1, 0.4, 0.2, 0.7, 1.0, 0.5, 0]
    ]
    
    pattern = random.choice(scroll_patterns)
    for scroll_pos in pattern:
        try:
            new_page.evaluate(f"window.scrollTo(0, document.body.scrollHeight*{scroll_pos})")
            time.sleep(random.uniform(0.5, 1.5))
        except Exception:
            break
    
    # Strategy 3: Random mouse movements
    try:
        for _ in range(random.randint(2, 5)):
            x = random.randint(100, 800)
            y = random.randint(100, 600)
            new_page.mouse.move(x, y)
            time.sleep(random.uniform(0.1, 0.3))
    except Exception:
        pass
    
    # Strategy 4: Wait for lazy-loaded content
    try:
        new_page.wait_for_load_state("networkidle", timeout=5000)
    except Exception:
        pass
    
    return True


def scrape_card_detail(card, page, scroll_pause, selectors, parse_utils):
    """Scrape detail satu card dengan anti-bot detection."""
    safe_get_text = parse_utils.safe_get_text
    safe_get_list = parse_utils.safe_get_list
    smart_kategorisasi = parse_utils.smart_kategorisasi
    extract_landmarks = parse_utils.extract_landmarks

    # Pre-click delay
    time.sleep(random.uniform(1, 3))

    with page.context.expect_page(timeout=15000) as new_page_info:
        card.click()
    new_page = new_page_info.value
    
    # Wait for page load
    try:
        new_page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass  # Continue silently

    # Initial scroll
    for scroll_pos in scroll_pause:
        new_page.evaluate(f"window.scrollTo(0, document.body.scrollHeight*{scroll_pos})")
        time.sleep(random.uniform(1.5, 3))

    # Parse data
    room_data = {
        "nama_kos": safe_get_text(new_page, selectors["room_name"]),
        "jenis_kos": safe_get_text(new_page, selectors["gender"]),
        "area": safe_get_text(new_page, selectors["area"]),
        "rating": safe_get_text(new_page, selectors["rating"]),
        "jumlah_review": safe_get_text(new_page, selectors["review_count"]),
        "total_transaksi": safe_get_text(new_page, selectors["transaction_count"]),
        "harga": safe_get_text(new_page, selectors["price"]),
        "periode": safe_get_text(new_page, selectors["period"]),
        "alamat": safe_get_text(new_page, selectors["address"]),
        "url": new_page.url,
        "scraped_at": datetime.now().isoformat()
    }
    
    # Bot detection check
    bot_detected = detect_bot_block(room_data)
    retry_count = 0
    max_retry = 2
    
    while bot_detected and retry_count < max_retry:
        # Clean bot detection message
        print(f"    - [Bot Detection: Retry {retry_count + 1}/{max_retry}]")
        
        if not handle_bot_detection(new_page, retry_count, max_retry):
            break
            
        # Re-parse after anti-detection
        room_data.update({
            "nama_kos": safe_get_text(new_page, selectors["room_name"]),
            "jenis_kos": safe_get_text(new_page, selectors["gender"]),
            "area": safe_get_text(new_page, selectors["area"]),
            "rating": safe_get_text(new_page, selectors["rating"]),
            "jumlah_review": safe_get_text(new_page, selectors["review_count"]),
            "total_transaksi": safe_get_text(new_page, selectors["transaction_count"]),
            "harga": safe_get_text(new_page, selectors["price"]),
            "periode": safe_get_text(new_page, selectors["period"]),
            "alamat": safe_get_text(new_page, selectors["address"]),
        })
        
        bot_detected = detect_bot_block(room_data)
        retry_count += 1
    
    # Skip if still blocked
    if bot_detected:
        new_page.close()
        raise Exception("Bot detection: Unable to parse content after retries")

    # Parse additional data
    fasilitas_list = safe_get_list(new_page, selectors["facilities"])
    room_data["fasilitas"] = smart_kategorisasi(fasilitas_list)
    room_data["peraturan"] = safe_get_list(new_page, selectors["rules"])
    room_data["landmarks"] = extract_landmarks(new_page)
    
    new_page.close()
    return room_data


def backup_region(region_results, region, backup_round, backup_folder):
    """Backup otomatis data region setiap interval tertentu."""
    os.makedirs(backup_folder, exist_ok=True)
    backup_path = f"{backup_folder}/{region}_{backup_round}.json"
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(region_results, f, ensure_ascii=False, indent=2)
    print(f"    * [Backup: Round {backup_round} | {len(region_results)} cards]")


def save_region(region_results, region, regions_folder):
    """Simpan data region setelah selesai scraping."""
    os.makedirs(regions_folder, exist_ok=True)
    region_path = f"{regions_folder}/{region}.json"
    with open(region_path, "w", encoding="utf-8") as f:
        json.dump(region_results, f, ensure_ascii=False, indent=2)
    region_short = region.split('-')[0].title()
    print(f"    ✓ [Save Region: {region_short} | {len(region_results)} cards]")


def save_failed_cards(failed_cards_info, region, failed_cards_folder):
    """Simpan info card yang tetap gagal setelah retry."""
    os.makedirs(failed_cards_folder, exist_ok=True)
    failed_path = f"{failed_cards_folder}/{region}_failed.json"
    with open(failed_path, "w", encoding="utf-8") as f:
        json.dump(failed_cards_info, f, ensure_ascii=False, indent=2)
    region_short = region.split('-')[0].title()
    print(f"    - [Failed Cards: {region_short} | {len(failed_cards_info)} items]")


def generate_master_file(regions_folder, data_dir, master_file):
    """Generate master file dari semua region files."""
    os.makedirs(data_dir, exist_ok=True)
    
    all_data = []
    region_files = glob.glob(f"{regions_folder}/*.json")
    
    print(f"  > Generating master file from {len(region_files)} regions...")
    
    for region_file in region_files:
        try:
            with open(region_file, "r", encoding="utf-8") as f:
                region_data = json.load(f)
                if isinstance(region_data, list):
                    all_data.extend(region_data)
                    region_name = os.path.basename(region_file).replace('.json', '').split('-')[0].title()
                    print(f"    - [Region: {region_name} | {len(region_data)} records]")
                else:
                    region_name = os.path.basename(region_file).replace('.json', '')
                    print(f"    X [Invalid Format: {region_name}]")
        except Exception as e:
            region_name = os.path.basename(region_file).replace('.json', '')
            print(f"    X [Read Error: {region_name} | {str(e)[:30]}...]")
    
    # Save master file
    master_path = f"{data_dir}/{master_file}"
    with open(master_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    print(f"  ✓ [Master File: {len(all_data)} total records]")
    return len(all_data)


def retry_failed_cards(
    failed_cards,
    page,
    scroll_pause,
    selectors,
    parse_utils,
    dedup,
    seen_keys,
    region_results,
    region,
    backup_interval,
    backup_round,
    backup_folder,
    duplicate_exit_threshold,
):
    """Retry scraping card yang gagal dengan enhanced anti-bot measures."""
    failed_cards_info = []
    duplicate_count = 0
    
    # Retry cooldown
    if failed_cards:
        cooldown = random.uniform(5, 15)
        print(f"    - [Retry Cooldown: {cooldown:.1f}s]")
        time.sleep(cooldown)
    
    for idx, card in failed_cards:
        try:
            room_data = scrape_card_detail(
                card, page, scroll_pause, selectors, parse_utils
            )
            dedup_key = (
                (room_data.get("nama_kos") or "").strip().lower(),
                (room_data.get("area") or "").strip().lower(),
                (room_data.get("alamat") or "").strip().lower(),
            )
            if dedup and dedup_key in seen_keys:
                print(f"    X [Duplicate: {room_data.get('nama_kos','Unknown')[:30]}...]")
                duplicate_count += 1
                if duplicate_count > duplicate_exit_threshold:
                    print("    X [Too Many Duplicates: Stopping retry]")
                    break
                continue
            seen_keys.add(dedup_key)
            region_results.append(room_data)
            print(f"    ✓ [Retry Success: {room_data['nama_kos'][:40]}...]")
            if len(region_results) % backup_interval == 0:
                backup_round += 1
                backup_region(region_results, region, backup_round, backup_folder)
        except Exception as e:
            print(f"    X [Retry Failed: Card {idx} | {str(e)[:30]}...]")
            failed_cards_info.append({"idx": idx, "error": str(e)})
    return failed_cards_info, backup_round
