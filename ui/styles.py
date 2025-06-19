SIMPLE_STYLES = {
     "main_window": """
        QWidget {
            background-color: #121212;
            font-family: 'Segoe UI', 'Arial', sans-serif;
            color: #E0E0E0;
            border: none;
        }
        QMainWindow {
            background-color: #121212;
        }
        QMainWindow::separator {
            background-color: #333333;
        }
    """,
    "window_frame": """
        QWidget {
            background-color: #1A1A1A;
            border: 1px solid #333333;
        }
    """,
    
    "title_bar": """
        QWidget {
            background-color: #1A1A1A;
            border-bottom: 1px solid #333333;
            min-height: 30px;
            max-height: 30px;
        }
    """,
    
    "title_bar_text": """
        QLabel {
            color: #FFFFFF;
            font-size: 12px;
            font-weight: bold;
            padding-left: 10px;
        }
    """,
    
    "title_bar_buttons": """
        QPushButton {
            background-color: transparent;
            border: none;
            color: #BBBBBB;
            font-size: 14px;
            min-width: 30px;
            max-width: 30px;
            min-height: 30px;
            max-height: 30px;
        }
        QPushButton:hover {
            background-color: #333333;
            color: #FFFFFF;
        }
        QPushButton#closeButton:hover {
            background-color: #FF4444;
            color: #FFFFFF;
        }
    """,
    "button_primary": """
        QPushButton {
            background-color: #4CAF50; /* Changed from #3373D9 to green */
            color: white;
            border-radius: 4px;
            padding: 8px 16px;
            border: none;
        }
        QPushButton:hover {
            background-color: #388E3C; /* Changed from #2A5CAA to darker green */
        }
    """,
        "secondary_button": """
        QPushButton {
            background-color: #2A73D9;  /* Mavi ton */
            color: #FFFFFF;
            border-radius: 4px;
            padding: 4px 8px;
            border: none;
        }
        QPushButton:hover {
            background-color: #1E5CB3;  /* Hover için daha koyu mavi */
        }
    """,
    "text_button": """
        QPushButton {
            background-color: transparent;
            border: none;
            color: #BBBBBB;
        }
        QPushButton:hover {
            color: #FFFFFF;
        }
    """,
    "quit_button": """
        QPushButton {
            background-color: #ff5252; 
            border: none;
            border-radius: 4px;
            padding: 6px 12px;
            color: white;
        }
        QPushButton:hover {
            background-color: #ff1744;
        }
    """,
    "text_link": """
        QPushButton {
            background-color: transparent;
            color: #4CAF50; /* Changed from #3373D9 to green */
            border: none;
        }
        QPushButton:hover {
            color: #66BB6A; /* Changed from #4080E0 to lighter green */
            text-decoration: underline;
        }
    """,
    "input_field": """
        QLineEdit {
            border: 1px solid #333333;
            border-radius: 4px;
            padding: 8px;
            background-color: #1E1E1E;
            color: #FFFFFF;
        }
        QLineEdit:focus {
            border-color: #4CAF50; /* Changed from #3373D9 to green */
        }
    """,
    "card": """
        QFrame {
            background-color: #1E1E1E;
            border-radius: 8px;
            border: 1px solid #333333;
            padding: 15px;
        }
    """,
    "sidebar": """
        QFrame {
            background-color: #1A1A1A;
            border-right: 1px solid #333333;
        }
    """,
    "sidebar_item": """
        QPushButton {
            background-color: transparent;
            color: #BBBBBB;
            border: none;
            text-align: left;
            padding: 10px 15px;
        }
        QPushButton:hover {
            background-color: #252525;
            color: #FFFFFF;
        }
        QPushButton:checked {
            background-color: #2A2A2A;
            color: #FFFFFF;
            border-left: 3px solid #4CAF50; /* Changed from #3373D9 to green */
        }
    """,
    "sidebar_item_active": """
         QPushButton {
             background-color: #4CAF50; /* Active background (already green) */
             color: #FFFFFF;
             font-weight: bold;
             border-left: 3px solid #4CAF50; /* Visual highlight (already green) */
             text-align: left;
             padding: 10px 15px;
         }
     """,
    "info_card": """
        QFrame {
            background-color: rgba(76, 175, 80, 0.1); /* Changed from rgba(51, 115, 217, 0.1) to green */
            border-radius: 6px;
            border: 1px solid rgba(76, 175, 80, 0.3); /* Changed from rgba(51, 115, 217, 0.3) to green */
            padding: 12px;
        }
    """,
    "upload_area": """
        QPushButton {
            border: 2px dashed #4CAF50; /* Changed from #3373D9 to green */
            border-radius: 6px;
            padding: 20px;
            color: #BBBBBB;
            background-color: #252525;
            text-align: center;
        }
        QPushButton:hover {
            background-color: #2A2A2A;
        }
    """,
    "scroll_area": """
        QScrollArea {
            background-color: #121212;
            border: none;
        }
        QScrollBar:vertical {
            background-color: #1A1A1A;
            width: 8px;
        }
        QScrollBar::handle:vertical {
            background-color: #333333;
            border-radius: 4px;
        }
    """,
    "brand_panel": """
        QFrame {
            background-color: #1A1A1A;
        }
    """,
    "login_panel": """
        QFrame {
            background-color: #121212;
        }
    """,
    "brand_title": """
        QLabel {
            font-size: 24px;
            font-weight: bold;
            color: #FFFFFF;
        }
    """,
    "brand_subtitle": """
        QLabel {
            font-size: 14px;
            color: #BBBBBB;
        }
    """,
    "form_title": """
        QLabel {
            font-size: 18px;
            font-weight: bold;
            color: #FFFFFF;
        }
    """,
    "header_text": """
        QLabel {
            font-size: 22px;
            color: #FFFFFF;
        }
    """,
    "close_button": """
        QPushButton {
            background-color: transparent;
            color: #999999;
            font-size: 16px;
            border: none;
            border-radius: 12px;
        }
        QPushButton:hover {
            background-color: #FF5252;
            color: white;
        }
    """,
    "user_profile": """
        QFrame {
            background-color: #252525;
            border-top: 1px solid #333333;
            padding: 10px;
            min-height: 50px; /* Add this line */
        }
    """,
    "logo_text": """
        QLabel {
            color: #FFFFFF;
            font-size: 16px;
            font-weight: bold;
        }
    """,
    "message_box": """
        QMessageBox {
            background-color: #1E1E1E;
            color: #E0E0E0;
        }
        QMessageBox QLabel {
            color: #E0E0E0;
        }
        QPushButton {
            background-color: #4CAF50; /* Changed from #3373D9 to green */
            color: white;
            border-radius: 4px;
            padding: 6px 12px;
            border: none;
        }
    """,
    "dialog": """
        QFileDialog {
            background-color: #1E1E1E;
            color: #E0E0E0;
        }
        QFileDialog QLabel {
            color: #E0E0E0;
        }
        QPushButton {
            background-color: #4CAF50; /* Changed from #3373D9 to green */
            color: white;
            border-radius: 4px;
            padding: 6px 12px;
        }
    """,
    "progress_bar": """
        QProgressBar {
            border: 1px solid #333333;
            border-radius: 5px;
            background-color: #1A1A1A;
            text-align: center;
            color: white; /* Text color for percentage */
        }
        QProgressBar::chunk {
            background-color: #4CAF50; /* Green progress (already green) */
            border-radius: 4px;
        }
    """,
    "frame_banner_card": """
        QFrame {
            background-color: #1E1E1E;
            border-radius: 6px;
            border: 1px solid #333333;
            padding: 5px;
            margin: 5px; /* Spacing between banners */
        }
    """,
    "frame_select_button": """
        QPushButton {
            background-color: #2F3136;
            color: #BBBBBB;
            border: 1px solid #444444;
            border-radius: 4px;
            padding: 5px;
        }
        QPushButton:hover {
            background-color: #36393F;
            color: #FFFFFF;
        }
        QPushButton:checked {
            background-color: #4CAF50; /* Changed from #3373D9 to green */
            color: #FFFFFF;
            border: 1px solid #4CAF50; /* Changed from #3373D9 to green */
            font-weight: bold;
        }
    """,
    "thumbnail_card": """
        QFrame {
            background-color: #1E1E1E;
            border-radius: 8px;
            border: 1px solid #333333;
            min-width: 100px; /* Minimum width for thumbnails */
            max-width: 200px; /* Maximum width for thumbnails */
            height: 250px; /* Fixed height for consistency */
        }
        QFrame:hover {
            border: 1px solid #4CAF50; /* Changed from #3373D9 to green */
        }
    """,
}