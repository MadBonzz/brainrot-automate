import unittest
from film import portrait


class PortraitTests(unittest.TestCase):
    def sheet(self):
        return dict(fps=30,width=720,height=1280,shots=[dict(clock=0,frames=150,shot=dict(
            actors=[dict(id='child'),dict(id='friend')],cameras=[
                dict(start=0,focus=['sign'],size=1.5,move='hold'),
                dict(start=0.15,focus=['child','friend'],size=2.3,move='follow'),
                dict(start=0.3,focus=['child'],size=1.9,move='hold'),
                dict(start=0.8,focus=['friend'],size=3.2,move='follow')]))])

    def test_cut_in_preserves_medium_lead_and_returns_to_native_on_the_cut(self):
        sheet=self.sheet()
        spans=portrait.angles(sheet)
        self.assertEqual(len(spans),1)
        frame=spans[0]
        self.assertEqual((frame['start'],frame['stop'],frame['cut_in']),(77,119,True))
        self.assertEqual(portrait.review(sheet,spans)['picture_shots'],5)
        self.assertIn('between(on,77,118)',portrait.filters(spans,720,1280,30)[0])
        self.assertEqual(portrait.filters([],720,1280,30),[])

    def test_fall_and_frozen_figures_keep_full_height(self):
        for override in (dict(lift=[0,-1.2]),dict(pose='frozen'),dict(pitch=[-48,0])):
            sheet=self.sheet()
            sheet['shots'][0]['shot']['actors'][0].update(override)
            self.assertEqual(portrait.angles(sheet),[])
