import unittest
from predash.portfolio import calculate, restore

class PortfolioTests(unittest.TestCase):
    def row(self, **kw):
        return dict({'종목':'테스트','분류':'해외ETF','수량':2,'평균매수가':100,'현재가':110,'환율':1400,'목표비중':50}, **kw)

    def test_conversion_and_cash_weight(self):
        r=calculate([self.row()],308000)
        self.assertEqual(r['total'],616000)
        self.assertEqual(r['pnl'],28000)
        self.assertAlmostEqual(r['rate'],10)
        self.assertEqual(r['rows'][0]['현재비중 (%)'],50)
        self.assertEqual(r['rows'][0]['목표대비 금액'],0)

    def test_zero_cost_and_empty(self):
        self.assertIsNone(calculate([])['rate'])
        self.assertIsNone(calculate([self.row(평균매수가=0)])['rows'][0]['수익률 (%)'])

    def test_invalid_input_and_target_total(self):
        for value in [-1,float('nan'),float('inf')]:
            with self.assertRaises(ValueError):calculate([self.row(현재가=value)])
        with self.assertRaises(ValueError):calculate([self.row(목표비중=60),self.row(목표비중=60)])
        with self.assertRaises(ValueError):restore('{"version":2,"holdings":[]}')

if __name__=='__main__':unittest.main()
