from ocr.detect_shop import wait_for_shop
from ocr.shop_monitor import monitor_shop_loop

if __name__ == "__main__":
    if wait_for_shop():
        monitor_shop_loop()