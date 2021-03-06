import unittest
from io import StringIO
from pyNastran.bdf.bdf import BDF
from pyNastran.bdf.cards.test.utils import save_load_deck
from pyNastran.bdf.cards.msgmesh import GMCORD, CGEN, GMLOAD
from cpylog import SimpleLogger

class TestMsgMesh(unittest.TestCase):

    def test_gmload(self):
        """tests GMLOAD"""
        log = SimpleLogger(level='warning')
        model = BDF(log=log)
        sid = 1
        normal = [1., 2., 3.]
        entity = 'cat'
        entity_id = 37
        method = 'frog'
        load_magnitudes = [31.]
        gmload = GMLOAD(sid, normal, entity, entity_id, method,
                    load_magnitudes, cid=0,
                    comment='gmload')
        gmload.raw_fields()
        gmload.validate()
        #model.cross_reference()
        #save_load_deck(model, run_convert=False)

    def test_gmcord(self):
        """tests GMCORD"""
        cid = 1
        entity = 'GMCURV'
        gm_ids = [3, 4]
        model = BDF(debug=False)
        gmcord = GMCORD(cid, entity, gm_ids)
        gmcord.raw_fields()
        str(gmcord)
        #save_load_deck(model, run_convert=False)

    def test_cgen(self):
        """tests CGEN"""
        log = SimpleLogger(level='warning')
        model = BDF(log=log, debug=False)
        model.add_grid(1, [0., 0., 0.])
        model.add_grid(2, [1., 0., 0.])
        model.add_grid(3, [1., 1., 0.])
        model.add_grid(4, [0., 1., 0.])
        #feedge = model.add_feedge()

        Type = 10
        field_eid = 'cat'
        pid = 20
        field_id = 30
        th_geom_opt = 301.
        eidl = 40
        eidh = 50
        cgen = CGEN(Type, field_eid, pid, field_id, th_geom_opt,
                    eidl, eidh)
        cgen.raw_fields()
        str(cgen)

        #----------------------------------------
        #bdf_filename = StringIO()
        #bdf_filename2 = StringIO()
        #bdf_filename3 = StringIO()
        ##bdf_filename4 = StringIO()

        #model.validate()
        #model._verify_bdf(xref=False)
        #model.write_bdf(bdf_filename, encoding=None, size=8,
                        #is_double=False,
                        #interspersed=False,
                        #enddata=None, close=False)

        #model.cross_reference()
        #model.pop_xref_errors()

        #model._verify_bdf(xref=True)
        #model.write_bdf(bdf_filename2, encoding=None, size=16,
                        #is_double=False,
                        #interspersed=False,
                        #enddata=None, close=False)
        #model.write_bdf(bdf_filename3, encoding=None, size=16,
                        #is_double=True,
                        #interspersed=False,
                        #enddata=None, close=False)
        ###model.cross_reference()

        ###print(bdf_filename.getvalue())

        ##bdf_filename2.seek(0)
        ##model2 = read_bdf(bdf_filename2, xref=False)
        ##print('---------------')
        ##model2.safe_cross_reference()
        #save_load_deck(model, run_convert=False, run_quality=False)

if __name__ == '__main__':  # pragma: no cover
    unittest.main()
