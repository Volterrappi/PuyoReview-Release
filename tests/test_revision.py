"""Record attachment and GUI regressions for the next analysis preview."""
import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'puyo_tools'))
import record_store
from PIL import Image
from app import App

EMPTY = ['......'] * 13


class ReferenceGroupingTests(unittest.TestCase):
    def test_grouping_preserves_every_shape_and_exact_metrics(self):
        from common.reference import multi_rows, group_equal_metrics
        source=multi_rows(5,False)
        grouped=group_equal_metrics(source)
        self.assertLess(len(grouped),len(source))
        self.assertEqual(sum(len(row['variants']) for row in grouped),len(source))
        self.assertEqual(len({(r['score'],r['efficiency']) for r in grouped}),len(grouped))
        self.assertEqual([r['efficiency'] for r in grouped],sorted(r['efficiency'] for r in grouped))
        original={(r['kind'],r['groups']):(r['score'],r['efficiency']) for r in source}
        for row in grouped:
            for shape in row['variants']:
                self.assertEqual(original[shape],(row['score'],row['efficiency']))
        self.assertNotIn('variants',source[0])


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


def button(window, text):
    return next(w for w in descendants(window)
                if w.winfo_class() in ('TButton', 'Button') and w.cget('text') == text)


class RevisionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root_patch = patch.object(record_store, 'ROOT', Path(self.temp.name))
        self.index_patch = patch.object(record_store, 'INDEX', Path(self.temp.name) / 'index.json')
        self.root_patch.start(); self.index_patch.start()
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(self.root_patch.stop); self.addCleanup(self.index_patch.stop)

    def test_attachments_survive_move_and_legacy_paths(self):
        item = record_store.save('未分類', 'test', '3手全探索', '', EMPTY,
            ['RB', 'GY', 'RP'], {}, Image.new('RGB', (8, 8), 'red'),
            iter([{'探索番号': 1, '得点': 123}, {'探索番号': 2, '得点': 456}]))
        self.assertEqual(item['screenshot'], 'screenshot.png')
        self.assertEqual(record_store.attachment(item['id'], 'csv_file').read_bytes()[:3], b'\xef\xbb\xbf')
        with record_store.attachment(item['id'], 'csv_file').open(encoding='utf-8-sig', newline='') as f:
            self.assertEqual(len(list(csv.DictReader(f))), 2)
        # Emulate a record created by the previous version.
        path = record_store.record_directory(item['id']) / 'record.json'
        item['screenshot'] = str(record_store.attachment(item['id'], 'screenshot'))
        path.write_text(json.dumps(item), encoding='utf-8')
        record_store.add_folder('移動先')
        record_store.move(item['id'], '移動先')
        self.assertTrue(record_store.attachment(item['id'], 'screenshot').is_file())
        self.assertTrue(record_store.attachment(item['id'], 'csv_file').is_file())

    def test_failed_csv_save_leaves_no_partial_record(self):
        def rows():
            yield {'得点': 1}
            raise OSError('disk error')
        with self.assertRaises(OSError):
            record_store.save('未分類', '', '3手全探索', '', EMPTY, [], {}, csv_rows=rows())
        self.assertEqual(record_store.list_records(), [])
        self.assertEqual(list((record_store.ROOT / '未分類').iterdir()), [])


class GuiRevisionTests(RevisionTests):
    def setUp(self):
        super().setUp()
        self.app = App()
        self.app.withdraw()
        self.app.update_idletasks()
        def close_app():
            for event_id in self.app.tk.call('after', 'info'):
                self.app.after_cancel(event_id)
            self.app.update_idletasks()
            self.app.destroy()
        self.addCleanup(close_app)
        self.messages = patch('app.messagebox.showinfo')
        self.messages.start(); self.addCleanup(self.messages.stop)

    def test_image_cancel_does_not_change_attachment_and_apply_does(self):
        red = Image.new('RGB', (300, 600), 'red')
        blue = Image.new('RGB', (300, 600), 'blue')
        self.app.imported_image = red
        self.app.image_import(source_image=blue)
        dialog = next(w for w in self.app.winfo_children() if w.winfo_class() == 'Toplevel')
        dialog.destroy()
        self.assertEqual(self.app.imported_image.getpixel((0, 0)), (255, 0, 0))
        with patch('app.recognize_board', return_value=tuple(EMPTY)):
            self.app.image_import(source_image=blue)
            dialog = next(w for w in self.app.winfo_children() if w.winfo_class() == 'Toplevel')
            button(dialog, '盤面に反映').invoke()
        self.assertEqual(self.app.imported_image.getpixel((0, 0)), (0, 0, 255))

    def test_saved_search_uses_search_next_board_image_and_csv(self):
        original = ['......'] * 12 + ['R.....']
        self.app.search_context = {'board': tuple(original), 'next_pairs': ('RB', 'GY', 'RP'),
            'initial_bonus': True, 'efficiency_bonus_mode': 'used', 'score_bonus': False,
            'image': Image.new('RGB', (8, 8), 'red')}
        self.app.search_board = tuple(original)
        self.app.review_mode = '3手全探索'
        self.app.results = [object(), object()]
        self.app.row_for = lambda i: {'得点': 100 + i}
        self.app.pairs_var.set('YY PP BB')
        self.app.imported_image = Image.new('RGB', (8, 8), 'blue')
        self.app.save_standalone()
        dialog = next(w for w in self.app.winfo_children() if w.winfo_class() == 'Toplevel')
        button(dialog,'探索時の盤面・NEXT（探索結果・CSV付き）').invoke()
        dialog = next(w for w in self.app.winfo_children() if w.winfo_class() == 'Toplevel')
        button(dialog, '保存').invoke()
        item = record_store.load(record_store.list_records()[0]['id'])
        self.assertEqual(item['next_pairs'], ['RB', 'GY', 'RP'])
        self.assertEqual(item['board'], original)
        self.assertTrue(item['analysis_result']['initial_bonus'])
        with Image.open(record_store.attachment(item['id'], 'screenshot')) as picture:
            self.assertEqual(picture.getpixel((0, 0)), (255, 0, 0))
        self.assertTrue(record_store.attachment(item['id'], 'csv_file').is_file())

    def test_reference_rows_and_record_actions(self):
        self.app.show_reference()
        texts = [str(w.cget('text')) for w in descendants(self.app)
                 if 'text' in w.keys()]
        next_page=[w for w in descendants(self.app) if w.winfo_class()=='TButton' and w.cget('text')=='次の36件 ▶'][-1]
        while not next_page.instate(['disabled']):
            next_page.invoke()
            texts.extend(str(w.cget('text')) for w in descendants(self.app) if 'text' in w.keys())
        for n in (3, 4, 5):
            self.assertIn(f'参考：{n}連鎖', texts)
        self.assertFalse(any('3連:' in text for text in texts))
        self.app.open_record_manager()
        manager = next(w for w in self.app.winfo_children()
                       if w.winfo_class() == 'Toplevel' and w.title() == '保存した記録の管理')
        for text in ('3手探索結果を開く（CSV）', '保存フォルダを開く'):
            self.assertTrue(button(manager, text).instate(['disabled']))
        table=next(w for w in descendants(manager) if w.winfo_class()=='Treeview')
        self.assertNotIn('number',table['columns'])
        self.assertFalse(any(w.winfo_class() == 'TButton' and w.cget('text') == '記録一覧をCSV保存'
                             for w in descendants(manager)))

    def test_restore_without_image_clears_previous_image_and_search(self):
        item = record_store.save('未分類', '画像なし', '盤面のみ', '', EMPTY, [], {})
        self.app.imported_image = Image.new('RGB', (8, 8), 'red')
        self.app.search_context = {'old': True}
        self.app.pairs_var.set('RR GG BB')
        self.app.open_record_manager()
        manager = next(w for w in self.app.winfo_children() if w.winfo_class() == 'Toplevel')
        table = next(w for w in descendants(manager) if w.winfo_class() == 'Treeview')
        table.selection_set(item['id'])
        table.event_generate('<<TreeviewSelect>>')
        self.app.update()
        button(manager, '盤面・NEXTを読み込む').invoke()
        self.assertIsNone(self.app.imported_image)
        self.assertIsNone(self.app.search_context)
        self.assertEqual(self.app.pairs_var.get(), '.. .. ..')
        self.assertEqual(self.app.results, [])

    def test_cancelled_or_invalid_search_keeps_completed_context(self):
        self.app.search_context = {'next_pairs': ('RB', 'GY', 'RP')}
        self.app.search_board = tuple(EMPTY)
        self.app.pairs_var.set('invalid')
        with patch('app.messagebox.showerror'):
            self.app.start_search()
        self.assertEqual(self.app.search_context['next_pairs'], ('RB', 'GY', 'RP'))
        self.assertFalse(self.app.search_running)

    def test_record_heading_sort_toggles_and_survives_refresh(self):
        for name in ('B記録','A記録'):
            record_store.save('未分類',name,'盤面のみ','',EMPTY,[],{})
        self.app.open_record_manager()
        manager=next(w for w in self.app.winfo_children() if w.winfo_class()=='Toplevel')
        table=next(w for w in descendants(manager) if w.winfo_class()=='Treeview')
        command=table.heading('name','command')
        table.tk.call(command)
        self.assertEqual([table.set(i,'name') for i in table.get_children()],['A記録','B記録'])
        table.tk.call(command)
        self.assertEqual([table.set(i,'name') for i in table.get_children()],['B記録','A記録'])
        button(manager,'一覧を更新').invoke()
        self.assertEqual([table.set(i,'name') for i in table.get_children()],['B記録','A記録'])

    def test_save_changed_input_preserves_original_results_and_csv(self):
        self.app.search_context={'board':tuple(EMPTY),'next_pairs':('RB','GY','RP'),
            'initial_bonus':False,'efficiency_bonus_mode':'used','score_bonus':False,'image':None}
        self.app.search_board=tuple(EMPTY)
        self.app.results=[object(),object()]
        self.app.cells=[list(row) for row in EMPTY[:-1]+['B.....']]
        self.app.review_mode='3手全探索'
        self.app.pairs_var.set('YY BB GG')
        self.app.save_standalone()
        choice=next(w for w in self.app.winfo_children() if w.winfo_class()=='Toplevel')
        self.app.row_for=lambda i:{'得点':100+i}
        with patch('app.solve') as solve:
            button(choice,'現在の盤面・NEXT＋前回の探索結果・CSV').invoke()
            solve.assert_not_called()
        dialog=next(w for w in self.app.winfo_children() if w.winfo_class()=='Toplevel')
        button(dialog,'保存').invoke()
        item=record_store.load(record_store.list_records()[0]['id'])
        self.assertEqual(item['next_pairs'],['YY','BB','GG'])
        self.assertEqual(item['analysis_type'],'3手全探索')
        self.assertEqual(item['board'][-1],'B.....')
        self.assertEqual(item['analysis_result']['analysis_input']['board'],EMPTY)
        self.assertEqual(item['analysis_result']['analysis_input']['next_pairs'],['RB','GY','RP'])
        self.assertTrue(item['analysis_result']['saved_input_differs'])
        self.assertTrue(record_store.attachment(item['id'],'csv_file').is_file())

    def test_analysis_status_tracks_board_next_and_return_to_original(self):
        self.app.tabs.select(self.app.tab2)
        self.app.update_analysis_status()
        self.assertIn('押してください',self.app.analysis_status.cget('text'))
        self.app.pairs_var.set('RB GY RP')
        self.app.search_context={'board':tuple(EMPTY),'next_pairs':('RB','GY','RP')}
        self.app.update_analysis_status()
        self.assertIn('入力中',self.app.analysis_status.cget('text'))
        self.app.cells[-1][0]='R';self.app.redraw_editor()
        self.assertIn('変更',self.app.analysis_status.cget('text'))
        self.app.cells[-1][0]='.';self.app.redraw_editor()
        self.assertIn('入力中',self.app.analysis_status.cget('text'))
        self.app.pairs_var.set('YY GY RP')
        self.assertIn('変更',self.app.analysis_status.cget('text'))

    def test_advanced_settings_start_collapsed_and_toggle(self):
        self.assertEqual(self.app.details_frame.winfo_manager(),'')
        self.app.toggle_details()
        self.assertEqual(self.app.details_frame.winfo_manager(),'pack')
        self.app.toggle_details()
        self.assertEqual(self.app.details_frame.winfo_manager(),'')

    def test_move_selects_existing_folder_without_typing(self):
        record_store.add_folder('移動先')
        item=record_store.save('未分類','test','盤面のみ','',EMPTY,[],{})
        self.app.open_record_manager()
        manager=next(w for w in self.app.winfo_children() if w.winfo_class()=='Toplevel')
        table=next(w for w in descendants(manager) if w.winfo_class()=='Treeview')
        table.selection_set(item['id']);table.event_generate('<<TreeviewSelect>>');self.app.update()
        button(manager,'記録を別フォルダへ移動').invoke()
        dialog=next(w for w in manager.winfo_children() if w.winfo_class()=='Toplevel')
        options=next(w for w in descendants(dialog) if w.winfo_class()=='Listbox')
        self.assertEqual(options.get(0),'移動先')
        button(dialog,'このフォルダへ移動').invoke()
        self.assertEqual(record_store.load(item['id'])['folder'],'移動先')


if __name__ == '__main__':
    unittest.main()
