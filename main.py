from ocr.detect_shop import wait_for_shop, shop_still_visible
from ocr.shop_monitor import monitor_shop_loop_once

def main():
    print("🟢 Starting TFT live monitor...")

    while True:
        # Step 1: Wait until shop appears
        if wait_for_shop():
            print("🔍 Monitoring shop...")

            # Step 2: While shop is visible, keep processing it
            while shop_still_visible():
                monitor_shop_loop_once()  # we'll fix this below

    

if __name__ == "__main__":
    main()