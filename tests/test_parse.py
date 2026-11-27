import unittest
from datetime import datetime

from cn_date.core import parse, parse_dt

NOW = datetime(2026, 3, 4, 10, 0)  # 周三


def dt(text, now=NOW):
    return parse_dt(text, now)


class TestRelativeDays(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(dt("今天"), datetime(2026, 3, 4, 9, 0))
        self.assertEqual(dt("明天"), datetime(2026, 3, 5, 9, 0))
        self.assertEqual(dt("后天"), datetime(2026, 3, 6, 9, 0))
        self.assertEqual(dt("大后天"), datetime(2026, 3, 7, 9, 0))

    def test_default_time_9am(self):
        r = parse("明天", NOW)
        self.assertFalse(r.has_time)
        self.assertEqual(r.dt.hour, 9)


class TestClock(unittest.TestCase):
    def test_combined(self):
        self.assertEqual(dt("明天下午3点"), datetime(2026, 3, 5, 15, 0))
        self.assertEqual(dt("明天下午3点半"), datetime(2026, 3, 5, 15, 30))
        self.assertEqual(dt("3天后晚上8点半"), datetime(2026, 3, 7, 20, 30))
        self.assertEqual(dt("下周一上午9点"), datetime(2026, 3, 9, 9, 0))
        self.assertEqual(dt("明天上午10点15分"), datetime(2026, 3, 5, 10, 15))

    def test_meridiem(self):
        self.assertEqual(dt("晚上8点").hour, 20)
        self.assertEqual(dt("中午12点").hour, 12)
        self.assertEqual(dt("中午12点30分"), datetime(2026, 3, 4, 12, 30))
        self.assertEqual(dt("凌晨2点").hour, 2)
        self.assertEqual(dt("凌晨12点").hour, 0)
        self.assertEqual(dt("晚上11点45分"), datetime(2026, 3, 4, 23, 45))

    def test_colon_form(self):
        self.assertEqual(dt("明天 14:30"), datetime(2026, 3, 5, 14, 30))

    def test_invalid_hour(self):
        for text in ("25点", "24点", "24点30分", "24:00", "中午24点",
                     "明天中午24点", "凌晨24点", "晚上24点", "10点75分"):
            with self.subTest(text=text):
                self.assertIsNone(dt(text))

    def test_numeric_boundaries(self):
        for text in ("123点", "10点123分", "14:300"):
            with self.subTest(text=text):
                self.assertIsNone(dt(text))

    def test_invalid_clock_with_date(self):
        for text in ("明天123点", "后天14:300", "下周10点123分"):
            with self.subTest(text=text):
                self.assertIsNone(dt(text))


class TestWeekday(unittest.TestCase):
    def test_this_week(self):
        # 周三(3/4) → 周五 = 3/6；周一已过 → 下周一 3/9
        self.assertEqual(dt("本周五"), datetime(2026, 3, 6, 9, 0))
        self.assertEqual(dt("周五"), datetime(2026, 3, 6, 9, 0))
        self.assertEqual(dt("周一"), datetime(2026, 3, 9, 9, 0))  # 已过 → 下周
        self.assertEqual(dt("周三"), datetime(2026, 3, 4, 9, 0))  # 今天

    def test_next_week(self):
        self.assertEqual(dt("下周一"), datetime(2026, 3, 9, 9, 0))
        self.assertEqual(dt("下周日"), datetime(2026, 3, 15, 9, 0))
        self.assertEqual(dt("下下周二"), datetime(2026, 3, 17, 9, 0))


class TestOffsets(unittest.TestCase):
    def test_days(self):
        self.assertEqual(dt("3天后"), datetime(2026, 3, 7, 9, 0))
        self.assertEqual(dt("30天后"), datetime(2026, 4, 3, 9, 0))
        self.assertEqual(dt("两周后"), datetime(2026, 3, 18, 9, 0))

    def test_months(self):
        self.assertEqual(dt("2个月后"), datetime(2026, 5, 4, 9, 0))
        self.assertEqual(dt("10个月后"), datetime(2027, 1, 4, 9, 0))

    def test_hours_minutes(self):
        self.assertEqual(dt("2小时后"), datetime(2026, 3, 4, 12, 0))
        self.assertEqual(dt("半小时后"), datetime(2026, 3, 4, 10, 30))
        self.assertEqual(dt("45分钟后"), datetime(2026, 3, 4, 10, 45))
        self.assertEqual(dt("两小时后"), datetime(2026, 3, 4, 12, 0))
        self.assertEqual(dt("俩小时后"), datetime(2026, 3, 4, 12, 0))

    def test_month_end_clamp(self):
        self.assertEqual(dt("1个月后", now=datetime(2026, 1, 31, 10, 0)),
                         datetime(2026, 2, 28, 9, 0))


class TestMonthDay(unittest.TestCase):
    def test_day_number(self):
        self.assertEqual(dt("15号"), datetime(2026, 3, 15, 9, 0))
        self.assertEqual(dt("本月20号"), datetime(2026, 3, 20, 9, 0))
        self.assertEqual(dt("下月5号"), datetime(2026, 4, 5, 9, 0))
        self.assertEqual(dt("31号", now=datetime(2026, 2, 10, 10, 0)),
                         datetime(2026, 2, 28, 9, 0))  # 钳到月末

    def test_month_end_word(self):
        self.assertEqual(dt("月底"), datetime(2026, 3, 31, 9, 0))

    def test_invalid_month_day(self):
        for text in ("0号", "00号", "下月0号", "131号"):
            with self.subTest(text=text):
                self.assertIsNone(dt(text))

    def test_invalid_month_day_with_date(self):
        for text in ("明天0号", "后天131号", "下周00号"):
            with self.subTest(text=text):
                self.assertIsNone(dt(text))


class TestTonightAndClean(unittest.TestCase):
    def test_tonight(self):
        self.assertEqual(dt("今晚"), datetime(2026, 3, 4, 20, 0))
        self.assertEqual(dt("今晚8点"), datetime(2026, 3, 4, 20, 0))

    def test_unparseable(self):
        self.assertIsNone(dt("随便说点什么"))
        self.assertIsNone(dt(""))
        self.assertIsNone(parse(None))

    def test_has_flags(self):
        r = parse("明天下午3点", NOW)
        self.assertTrue(r.has_date and r.has_time)
        r = parse("明天", NOW)
        self.assertTrue(r.has_date and not r.has_time)
        r = parse("18:00", NOW)
        self.assertFalse(r.has_date)
        self.assertTrue(r.has_time)


if __name__ == "__main__":
    unittest.main()
