#!/usr/bin/env python3
"""
Professional Music Player built with PyQt5
"""

import sys
import os
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QSlider, QLabel,
    QComboBox, QFileDialog, QMessageBox, QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl

try:
    from mutagen import File as MutagenFile
except ImportError:
    MutagenFile = None


class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Music Player')
        self.setGeometry(100, 100, 1000, 600)
        
        # Data structures
        self.playlist = []
        self.display_indices = []
        self.queue = []
        self.genres = set()
        
        self.current_index = None
        self.is_paused = False
        
        # Media player
        self.media_player = QMediaPlayer()
        self.media_player.mediaStatusChanged.connect(self._on_media_status_changed)
        self.media_player.durationChanged.connect(self._update_duration)
        self.media_player.positionChanged.connect(self._update_position)
        
        # UI timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._poll)
        self.timer.start(500)
        
        self._build_ui()
        self._apply_stylesheet()
        
    def _build_ui(self):
        """Build the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Left panel: Playlist
        left_panel = QVBoxLayout()
        
        playlist_label = QLabel('Playlist')
        playlist_label.setFont(QFont('Arial', 10, QFont.Bold))
        left_panel.addWidget(playlist_label)
        
        self.playlist_table = QTableWidget()
        self.playlist_table.setColumnCount(3)
        self.playlist_table.setHorizontalHeaderLabels(['Title', 'Genre', 'Comments'])
        self.playlist_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.playlist_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.playlist_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.playlist_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.playlist_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.playlist_table.doubleClicked.connect(self._on_playlist_double_click)
        left_panel.addWidget(self.playlist_table)
        
        # Middle panel: Queue
        middle_panel = QVBoxLayout()
        
        queue_label = QLabel('Queue')
        queue_label.setFont(QFont('Arial', 10, QFont.Bold))
        middle_panel.addWidget(queue_label)
        
        self.queue_table = QTableWidget()
        self.queue_table.setColumnCount(1)
        self.queue_table.setHorizontalHeaderLabels(['Upcoming'])
        self.queue_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        middle_panel.addWidget(self.queue_table)
        
        # Right panel: Controls
        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)
        
        btn_add_files = QPushButton('Add Files')
        btn_add_files.clicked.connect(self.add_files)
        right_panel.addWidget(btn_add_files)
        
        btn_add_folder = QPushButton('Add Folder')
        btn_add_folder.clicked.connect(self.add_folder)
        right_panel.addWidget(btn_add_folder)
        
        right_panel.addSpacing(10)
        
        genre_label = QLabel('Genre')
        genre_label.setFont(QFont('Arial', 9, QFont.Bold))
        right_panel.addWidget(genre_label)
        
        self.genre_combo = QComboBox()
        self.genre_combo.addItem('All')
        self.genre_combo.currentTextChanged.connect(self._apply_filter)
        right_panel.addWidget(self.genre_combo)
        
        right_panel.addSpacing(10)
        
        # Playback controls
        control_buttons_layout = QHBoxLayout()
        
        self.btn_prev = QPushButton('⏮ Prev')
        self.btn_prev.clicked.connect(self.prev_track)
        control_buttons_layout.addWidget(self.btn_prev)
        
        self.btn_play = QPushButton('▶ Play')
        self.btn_play.clicked.connect(self.play_pause)
        control_buttons_layout.addWidget(self.btn_play)
        
        self.btn_stop = QPushButton('⏹ Stop')
        self.btn_stop.clicked.connect(self.stop)
        control_buttons_layout.addWidget(self.btn_stop)
        
        self.btn_next = QPushButton('Next ⏭')
        self.btn_next.clicked.connect(self.next_track)
        control_buttons_layout.addWidget(self.btn_next)
        
        right_panel.addLayout(control_buttons_layout)
        
        right_panel.addSpacing(10)
        
        # Volume control
        volume_label = QLabel('Volume')
        volume_label.setFont(QFont('Arial', 9, QFont.Bold))
        right_panel.addWidget(volume_label)
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        right_panel.addWidget(self.volume_slider)
        
        right_panel.addSpacing(10)
        
        self.time_label = QLabel('00:00 / 00:00')
        self.time_label.setFont(QFont('Courier', 9))
        self.time_label.setAlignment(Qt.AlignCenter)
        right_panel.addWidget(self.time_label)
        
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 100)
        self.progress_slider.sliderMoved.connect(self._on_seek)
        right_panel.addWidget(self.progress_slider)
        
        right_panel.addSpacing(10)
        
        self.status_label = QLabel('Ready')
        self.status_label.setFont(QFont('Arial', 9))
        self.status_label.setWordWrap(True)
        right_panel.addWidget(self.status_label)
        
        right_panel.addStretch()
        
        # Add panels to main layout
        main_layout.addLayout(left_panel, 2)
        main_layout.addLayout(middle_panel, 1)
        main_layout.addLayout(right_panel, 1)
        
    def _apply_stylesheet(self):
        """Apply modern dark theme stylesheet"""
        stylesheet = """
        QMainWindow { background-color: #1e1e1e; color: #ffffff; }
        QWidget { background-color: #1e1e1e; color: #ffffff; }
        QPushButton { background-color: #0078d4; color: white; border: none; border-radius: 4px; padding: 8px; font-weight: bold; font-size: 11px; }
        QPushButton:hover { background-color: #1084d7; }
        QPushButton:pressed { background-color: #106ebe; }
        QTableWidget { background-color: #2d2d2d; alternate-background-color: #252525; gridline-color: #3d3d3d; border: none; }
        QTableWidget::item { padding: 4px; }
        QTableWidget::item:selected { background-color: #0078d4; }
        QHeaderView::section { background-color: #1e1e1e; color: #ffffff; padding: 5px; border: none; border-right: 1px solid #3d3d3d; border-bottom: 1px solid #3d3d3d; }
        QComboBox { background-color: #2d2d2d; color: #ffffff; border: 1px solid #3d3d3d; border-radius: 4px; padding: 5px; }
        QComboBox::drop-down { border: none; background-color: #0078d4; width: 30px; }
        QComboBox QAbstractItemView { background-color: #2d2d2d; color: #ffffff; selection-background-color: #0078d4; }
        QSlider::groove:horizontal { border: 1px solid #3d3d3d; height: 8px; margin: 2px 0; background-color: #2d2d2d; border-radius: 4px; }
        QSlider::handle:horizontal { background-color: #0078d4; border: none; width: 16px; margin: -4px 0; border-radius: 8px; }
        QSlider::handle:horizontal:hover { background-color: #1084d7; }
        QLabel { color: #ffffff; }
        """
        self.setStyleSheet(stylesheet)
        
    def add_files(self):
        """Add individual audio files to playlist"""
        files, _ = QFileDialog.getOpenFileNames(
            self, 'Select audio files', '',
            'Audio Files (*.mp3 *.wav *.ogg *.flac *.m4a);;All Files (*)'
        )
        for file in files:
            self._add_path(file)
            
    def add_folder(self):
        """Recursively add all audio files from a folder"""
        folder = QFileDialog.getExistingDirectory(self, 'Select a folder')
        if folder:
            audio_extensions = {'.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac'}
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if Path(file).suffix.lower() in audio_extensions:
                        self._add_path(os.path.join(root, file))
                        
    def _add_path(self, path):
        """Add a single track to the playlist"""
        if any(t['path'] == path for t in self.playlist):
            return
            
        title = os.path.basename(path)
        genre = 'Unknown'
        comment = ''
        
        if MutagenFile is not None:
            try:
                tags = MutagenFile(path, easy=True)
                if tags is not None:
                    title = tags.get('title', [title])[0]
                    genre = tags.get('genre', [genre])[0]
                    comment_val = tags.get('comment', [''])[0]
                    comment = str(comment_val) if comment_val else ''
            except Exception:
                pass
                
        entry = {
            'path': path,
            'title': title,
            'basename': os.path.basename(path),
            'genre': genre,
            'comment': comment
        }
        self.playlist.append(entry)
        self.genres.add(genre)
        self._update_genre_options()
        self._apply_filter()
        
    def _update_genre_options(self):
        """Update genre filter dropdown"""
        current = self.genre_combo.currentText()
        self.genre_combo.blockSignals(True)
        self.genre_combo.clear()
        self.genre_combo.addItem('All')
        for genre in sorted(g for g in self.genres if g):
            self.genre_combo.addItem(genre)
        self.genre_combo.blockSignals(False)
        if current in [self.genre_combo.itemText(i) for i in range(self.genre_combo.count())]:
            self.genre_combo.setCurrentText(current)
            
    def _apply_filter(self):
        """Filter playlist by selected genre"""
        genre = self.genre_combo.currentText()
        self.display_indices = []
        self.playlist_table.setRowCount(0)
        
        for idx, entry in enumerate(self.playlist):
            if genre == 'All' or entry['genre'] == genre:
                row = self.playlist_table.rowCount()
                self.playlist_table.insertRow(row)
                
                title_item = QTableWidgetItem(entry['title'])
                genre_item = QTableWidgetItem(entry['genre'])
                comment_item = QTableWidgetItem(entry['comment'])
                
                self.playlist_table.setItem(row, 0, title_item)
                self.playlist_table.setItem(row, 1, genre_item)
                self.playlist_table.setItem(row, 2, comment_item)
                
                self.display_indices.append(idx)
                
    def _on_playlist_double_click(self, index):
        """Handle double-click on playlist"""
        row = index.row()
        if 0 <= row < len(self.display_indices):
            playlist_idx = self.display_indices[row]
            self.current_index = playlist_idx
            self._load_and_play(playlist_idx)
            
    def _load_and_play(self, index):
        """Load and play a track"""
        if index < 0 or index >= len(self.playlist):
            return
            
        path = self.playlist[index]['path']
        try:
            media = QMediaContent(QUrl.fromLocalFile(path))
            self.media_player.setMedia(media)
            self.media_player.play()
            self.current_index = index
            self._update_status()
            self.btn_play.setText('⏸ Pause')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Could not play track: {e}')
            
    def play_pause(self):
        """Toggle play/pause"""
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.btn_play.setText('▶ Play')
            self.is_paused = True
        elif self.is_paused:
            self.media_player.play()
            self.btn_play.setText('⏸ Pause')
            self.is_paused = False
        else:
            if self.current_index is None:
                if self.playlist:
                    self.current_index = self.display_indices[0] if self.display_indices else 0
                else:
                    QMessageBox.information(self, 'Empty', 'Add some tracks first')
                    return
            self._load_and_play(self.current_index)
            
    def stop(self):
        """Stop playback"""
        self.media_player.stop()
        self.btn_play.setText('▶ Play')
        self.is_paused = False
        self.status_label.setText('Stopped')
        self.time_label.setText('00:00 / 00:00')
        
    def next_track(self):
        """Play next track"""
        if not self.playlist:
            return
            
        if self.queue:
            next_idx = self.queue.pop(0)
            self._update_queue_display()
        else:
            if self.genre_combo.currentText() != 'All' and self.display_indices:
                try:
                    pos = self.display_indices.index(self.current_index)
                    next_pos = (pos + 1) % len(self.display_indices)
                    next_idx = self.display_indices[next_pos]
                except (ValueError, IndexError):
                    next_idx = self.display_indices[0] if self.display_indices else 0
            else:
                next_idx = (self.current_index + 1) % len(self.playlist) if self.current_index is not None else 0
                
        self._load_and_play(next_idx)
        
    def prev_track(self):
        """Play previous track"""
        if not self.playlist:
            return
            
        if self.genre_combo.currentText() != 'All' and self.display_indices:
            try:
                pos = self.display_indices.index(self.current_index)
                prev_pos = (pos - 1) % len(self.display_indices)
                prev_idx = self.display_indices[prev_pos]
            except (ValueError, IndexError):
                prev_idx = self.display_indices[-1] if self.display_indices else 0
        else:
            prev_idx = (self.current_index - 1) % len(self.playlist) if self.current_index is not None else len(self.playlist) - 1
            
        self._load_and_play(prev_idx)
        
    def _on_volume_changed(self, value):
        """Handle volume slider change"""
        self.media_player.setVolume(value)
        
    def _on_seek(self, position):
        """Handle seek slider movement"""
        self.media_player.setPosition(position)
        
    def _update_position(self, position):
        """Update position display and slider"""
        if self.media_player.duration() > 0:
            self.progress_slider.blockSignals(True)
            self.progress_slider.setValue(position)
            self.progress_slider.blockSignals(False)
            
            current_sec = position // 1000
            total_sec = self.media_player.duration() // 1000
            current_time = f'{current_sec // 60:02d}:{current_sec % 60:02d}'
            total_time = f'{total_sec // 60:02d}:{total_sec % 60:02d}'
            self.time_label.setText(f'{current_time} / {total_time}')
            
    def _update_duration(self, duration):
        """Update progress slider range"""
        self.progress_slider.setRange(0, duration)
        
    def _on_media_status_changed(self):
        """Handle media status changes"""
        if self.media_player.mediaStatus() == QMediaPlayer.EndOfMedia:
            self.next_track()
            
    def _update_status(self):
        """Update status label"""
        if self.current_index is not None and 0 <= self.current_index < len(self.playlist):
            track = self.playlist[self.current_index]
            self.status_label.setText(f"Playing: {track['title']}")
            
    def _poll(self):
        pass
        
    def _on_queue_context_menu(self, position):
        """Handle right-click on queue"""
        item = self.queue_table.itemAt(position)
        if item:
            row = item.row()
            if 0 <= row < len(self.queue):
                self.queue.pop(row)
                self._update_queue_display()
                
    def _update_queue_display(self):
        """Update queue table"""
        self.queue_table.setRowCount(0)
        for playlist_idx in self.queue:
            if 0 <= playlist_idx < len(self.playlist):
                row = self.queue_table.rowCount()
                self.queue_table.insertRow(row)
                title = self.playlist[playlist_idx]['title']
                self.queue_table.setItem(row, 0, QTableWidgetItem(title))


def main():
    app = QApplication(sys.argv)
    player = MusicPlayer()
    player.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
