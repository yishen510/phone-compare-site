import unittest

from price_server import offer_matches_sku, parse_price, reject_offer, safe_offer_url


class QuoteValidationTests(unittest.TestCase):
    def test_storage_pair_matches_exact_target(self):
        self.assertTrue(offer_matches_sku("小米 15 Ultra 12GB+256GB 全新国行", "12GB+256GB"))
        self.assertTrue(offer_matches_sku("小米15 Ultra 12GB 内存 256GB 存储", "12GB+256GB"))
        self.assertFalse(offer_matches_sku("小米 15 Ultra 16GB+512GB", "12GB+256GB"))

    def test_iphone_storage_matches_without_false_digit_substring(self):
        self.assertTrue(offer_matches_sku("Apple iPhone 17 Pro Max 256GB", "256GB"))
        self.assertFalse(offer_matches_sku("Apple iPhone 17 Pro Max 1256GB", "256GB"))
        self.assertFalse(offer_matches_sku("Apple iPhone 17 Pro Max 512GB", "256GB"))

    def test_price_parser_rejects_missing_or_implausible_prices(self):
        self.assertEqual(parse_price("¥5,999.00"), 5999.0)
        self.assertIsNone(parse_price("价格待核验"))
        self.assertIsNone(parse_price("99"))

    def test_unsafe_offer_urls_are_rejected(self):
        self.assertTrue(safe_offer_url("https://shop.example/item/1"))
        self.assertFalse(safe_offer_url("http://shop.example/item/1"))
        self.assertFalse(safe_offer_url("javascript:alert(1)"))
        self.assertFalse(safe_offer_url("not-a-url"))

    def test_used_and_accessory_listings_are_rejected(self):
        terms = ["二手", "翻新", "保护壳", "贴膜", "以旧换新价"]
        self.assertTrue(reject_offer("小米15 Ultra 二手 12GB+256GB", terms))
        self.assertTrue(reject_offer("小米15 Ultra 保护壳", terms))
        self.assertFalse(reject_offer("小米15 Ultra 全新国行", terms))


if __name__ == "__main__":
    unittest.main()
