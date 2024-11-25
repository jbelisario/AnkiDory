print("\n=== LOADING DEVELOPMENT VERSION OF TOOLBAR.PY ===\n")

# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
from __future__ import annotations

import enum
import re
import sys
import logging
import os
from collections.abc import Callable
from typing import Any, cast

import aqt
from anki.sync import SyncStatus
from aqt import gui_hooks, props
from aqt.qt import *
from aqt.sync import get_sync_status
from aqt.theme import theme_manager
from aqt.utils import tooltip, tr
from aqt.webview import AnkiWebView, AnkiWebViewKind
from aqt.ai_settings.settings import AISettings, AISettingsDialog
from ..gui.generate_deck_dialog import GenerateDeckDialog

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class HideMode(enum.IntEnum):
    FULLSCREEN = 0
    ALWAYS = 1


# wrapper class for set_bridge_command()
class TopToolbar:
    def __init__(self, toolbar: Toolbar) -> None:
        self.toolbar = toolbar


# wrapper class for set_bridge_command()
class BottomToolbar:
    def __init__(self, toolbar: Toolbar) -> None:
        self.toolbar = toolbar


class ToolbarWebView(AnkiWebView):
    hide_condition: Callable[..., bool]

    def __init__(
        self, mw: aqt.AnkiQt, kind: AnkiWebViewKind = AnkiWebViewKind.DEFAULT
    ) -> None:
        AnkiWebView.__init__(self, mw, kind=kind)
        self.mw = mw
        self.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        self.disable_zoom()
        self.hidden = False
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.reset_timer()

    def reset_timer(self) -> None:
        self.hide_timer.stop()
        self.hide_timer.setInterval(2000)

    def hide(self) -> None:
        self.hidden = True

    def show(self) -> None:
        self.hidden = False


class TopWebView(ToolbarWebView):
    def __init__(self, mw: aqt.AnkiQt) -> None:
        super().__init__(mw, kind=AnkiWebViewKind.TOP_TOOLBAR)
        self.web_height = 0
        qconnect(self.hide_timer.timeout, self.hide_if_allowed)
        logger.debug("\n=== TopWebView Initialization Debug ===")

    def eventFilter(self, obj, evt):
        if handled := super().eventFilter(obj, evt):
            return handled

        # prevent collapse of both toolbars if pointer is inside one of them
        if evt.type() == QEvent.Type.Enter:
            self.reset_timer()
            self.mw.bottomWeb.reset_timer()
            return True

        return False

    def on_body_classes_need_update(self) -> None:
        super().on_body_classes_need_update()

        if self.mw.state == "review":
            if self.mw.pm.hide_top_bar():
                self.eval("""document.body.classList.remove("flat"); """)
            else:
                self.flatten()

        self.show()

    def _onHeight(self, qvar: int | None) -> None:
        super()._onHeight(qvar)
        if qvar:
            self.web_height = int(qvar)

    def hide_if_allowed(self) -> None:
        if self.mw.state != "review":
            return

        if self.mw.pm.hide_top_bar():
            if (
                self.mw.pm.top_bar_hide_mode() == HideMode.FULLSCREEN
                and not self.mw.windowState() & Qt.WindowState.WindowFullScreen
            ):
                self.show()
                return

            self.hide()

    def hide(self) -> None:
        super().hide()

        self.hidden = True
        self.eval(
            """document.body.classList.add("hidden"); """,
        )
        if self.mw.fullscreen:
            self.mw.hide_menubar()

    def show(self) -> None:
        super().show()

        self.eval("""document.body.classList.remove("hidden"); """)
        self.mw.show_menubar()

    def flatten(self) -> None:
        self.eval("""document.body.classList.add("flat"); """)

    def elevate(self) -> None:
        self.eval(
            """
            document.body.classList.remove("flat");
            document.body.style.removeProperty("background");
            """
        )

    def update_background_image(self) -> None:
        if self.mw.pm.minimalist_mode():
            return

        def set_background(computed: str) -> None:
            # remove offset from copy
            background = re.sub(r"-\d+px ", "0%", computed)
            # ensure alignment with main webview
            background = re.sub(r"\sfixed", "", background)
            # change computedStyle px value back to 100vw
            background = re.sub(r"\d+px", "100vw", background)

            self.eval(
                f"""
                    document.body.style.setProperty("background", '{background}');
                """
            )
            self.set_body_height(self.mw.web.height())

            # offset reviewer background by toolbar height
            if self.web_height:
                self.mw.web.eval(
                    f"""document.body.style.setProperty("background-position-y", "-{self.web_height}px"); """
                )

        self.mw.web.evalWithCallback(
            """window.getComputedStyle(document.body).background; """,
            set_background,
        )

    def set_body_height(self, height: int) -> None:
        self.eval(
            f"""document.body.style.setProperty("min-height", "{self.mw.web.height()}px"); """
        )

    def adjustHeightToFit(self) -> None:
        self.eval("""document.body.style.setProperty("min-height", "0px"); """)
        self.evalWithCallback("document.documentElement.offsetHeight", self._onHeight)

    def resizeEvent(self, event: QResizeEvent | None) -> None:
        super().resizeEvent(event)

        self.mw.web.evalWithCallback(
            """window.innerHeight; """,
            self.set_body_height,
        )


class BottomWebView(ToolbarWebView):
    def __init__(self, mw: aqt.AnkiQt) -> None:
        super().__init__(mw, kind=AnkiWebViewKind.BOTTOM_TOOLBAR)
        qconnect(self.hide_timer.timeout, self.hide_if_allowed)
        logger.debug("\n=== BottomWebView Initialization Debug ===")

    def eventFilter(self, obj, evt):
        if handled := super().eventFilter(obj, evt):
            return handled

        if evt.type() == QEvent.Type.Enter:
            self.reset_timer()
            self.mw.toolbarWeb.reset_timer()
            return True

        return False

    def on_body_classes_need_update(self) -> None:
        super().on_body_classes_need_update()
        if self.mw.state == "review":
            self.show()

    def animate_height(self, height: int) -> None:
        self.web_height = height

        if self.mw.pm.reduce_motion() or height == self.height():
            self.setFixedHeight(height)
        else:
            # Collapse/Expand animation
            self.setMinimumHeight(0)
            self.animation = QPropertyAnimation(
                self, cast(QByteArray, b"maximumHeight")
            )
            self.animation.setDuration(int(theme_manager.var(props.TRANSITION)))
            self.animation.setStartValue(self.height())
            self.animation.setEndValue(height)
            qconnect(self.animation.finished, lambda: self.setFixedHeight(height))
            self.animation.start()

    def hide_if_allowed(self) -> None:
        if self.mw.state != "review":
            return

        if self.mw.pm.hide_bottom_bar():
            if (
                self.mw.pm.bottom_bar_hide_mode() == HideMode.FULLSCREEN
                and not self.mw.windowState() & Qt.WindowState.WindowFullScreen
            ):
                self.show()
                return

            self.hide()

    def hide(self) -> None:
        super().hide()

        self.hidden = True
        self.animate_height(1)

    def show(self) -> None:
        super().show()

        self.hidden = False
        if self.mw.state == "review":
            self.evalWithCallback(
                "document.documentElement.offsetHeight", self.animate_height
            )
        else:
            self.adjustHeightToFit()


class Toolbar:
    """Toolbar for Anki's main window."""

    def __init__(self, mw: aqt.AnkiQt, web: AnkiWebView) -> None:
        logger.debug("=== Initializing Toolbar ===")
        self.mw = mw
        self.web = web
        self.ai_settings = AISettings(mw)
        
        # Initialize link handlers
        self.link_handlers: dict[str, Callable] = {}
        self._register_default_handlers()
        
        self.web.requiresCol = False
        logger.debug("Toolbar initialization complete")
    
    def _register_default_handlers(self) -> None:
        """Register all default link handlers."""
        logger.debug("Registering default link handlers")
        handlers = {
            "study": self._studyLinkHandler,
            "decks": self._deckLinkHandler,
            "add": self._addLinkHandler,
            "browse": self._browseLinkHandler,
            "stats": self._statsLinkHandler,
            "generate_deck": self._generateDeckLinkHandler,
            "ai_settings": self._aiSettingsLinkHandler,
            "sync": self._syncLinkHandler,
        }
        self.link_handlers.update(handlers)
        logger.debug(f"Registered handlers: {list(self.link_handlers.keys())}")

    def draw(
        self,
        buf: str = "",
        web_context: Any | None = None,
        link_handler: Callable[[str], Any] | None = None,
    ) -> None:
        logger.debug("\n=== Drawing Toolbar ===")
        web_context = web_context or TopToolbar(self)
        link_handler = link_handler or self._linkHandler
        
        logger.debug("Setting up bridge command")
        self.web.set_bridge_command(link_handler, web_context)
        
        # Build toolbar content
        logger.debug("Building toolbar content")
        toolbar_content = self._centerLinks()
        left_tray = self._left_tray_content()
        right_tray = self._right_tray_content()
        
        # Format HTML
        logger.debug("Formatting HTML")
        body = self._body.format(
            toolbar_content=toolbar_content,
            left_tray_content=left_tray,
            right_tray_content=right_tray,
        )
        
        # Add custom CSS
        custom_css = """
        <style>
        /* Debug border to see element boundaries */
        .toolbar-item {
            display: inline-block !important;
            margin: 0 4px !important;
            vertical-align: middle !important;
            border: 1px solid red;  /* Debug border */
        }
        .hitem {
            display: inline-block !important;
            padding: 5px 10px !important;
            color: inherit !important;
            text-decoration: none !important;
            border: 1px solid blue;  /* Debug border */
        }
        .ai-settings-button {
            display: inline-block !important;
            margin: 0 8px !important;
            border: 2px solid green !important;  /* Debug border */
        }
        </style>
        """
        
        # Log the final HTML
        logger.debug("Final HTML structure:")
        logger.debug(custom_css + body)
        
        # Render toolbar
        logger.debug("Rendering toolbar")
        self.web.stdHtml(
            custom_css + body,
            css=["css/toolbar.css"],
            js=["js/vendor/jquery.min.js", "js/toolbar.js"],
            context=web_context,
        )
        
        # Force update
        logger.debug("Forcing toolbar update")
        self.web.eval("updateToolbar();")
        self.web.adjustHeightToFit()
        self.update_sync_status()
        logger.debug("Toolbar draw complete")

    def _centerLinks(self) -> str:
        """Build HTML for the center links."""
        logger.debug("\n=== Generating Toolbar Buttons ===")
        
        links = []
        for button_info in [
            ("decks", tr.actions_decks(), self._deckLinkHandler, "D"),
            ("add", tr.actions_add(), self._addLinkHandler, "A"),
            ("browse", tr.qt_misc_browse(), self._browseLinkHandler, "B"),
            ("stats", tr.qt_misc_stats(), self._statsLinkHandler, "T"),
            ("generate_deck", "Generate Deck with AI", self._generateDeckLinkHandler, "G"),
            ("ai_settings", "AI Settings", self._aiSettingsLinkHandler, "I"),
            ("sync", self._syncLabel(), self._syncLinkHandler, "Y"),
        ]:
            cmd, label, handler, shortcut = button_info
            logger.debug(f"\nGenerating button: {cmd}")
            logger.debug(f"Label: {label}")
            logger.debug(f"Handler: {handler.__name__}")
            
            link = self.create_link(
                cmd,
                label,
                handler,
                tip=tr.actions_shortcut_key(val=shortcut) if cmd != "ai_settings" else "Configure AI settings (Alt+I)",
                id=cmd,
                class_=f"{cmd}-button" if cmd == "ai_settings" else None,
            )
            logger.debug(f"Generated HTML: {link}")
            links.append(link)

        # Let add-ons modify the link list
        logger.debug("\nBefore add-on modifications:")
        logger.debug(f"Number of links: {len(links)}")
        logger.debug(f"Link IDs: {[re.search(r'id="([^"]+)"', link).group(1) if re.search(r'id="([^"]+)"', link) else None for link in links]}")
        
        gui_hooks.top_toolbar_did_init_links(links, self)
        
        logger.debug("\nAfter add-on modifications:")
        logger.debug(f"Number of links: {len(links)}")
        logger.debug(f"Link IDs: {[re.search(r'id="([^"]+)"', link).group(1) if re.search(r'id="([^"]+)"', link) else None for link in links]}")

        # Join links with debug borders
        html = "\n".join(f'<div class="toolbar-item">{link}</div>' for link in links)
        logger.debug("\nFinal HTML structure:")
        logger.debug(html)
        
        return html

    def _linkHandler(self, link: str) -> bool:
        """Handle clicks on toolbar links."""
        logger.debug(f"\n=== Link Handler Called ===")
        logger.debug(f"Received link command: {link}")
        logger.debug(f"Available handlers: {list(self.link_handlers.keys())}")
        
        if link in self.link_handlers:
            logger.debug(f"Found handler for {link}: {self.link_handlers[link].__name__}")
            self.link_handlers[link]()
            logger.debug(f"Handler executed for {link}")
        else:
            logger.debug(f"No handler found for link: {link}")
        
        return False

    def _deckLinkHandler(self) -> None:
        self.mw.moveToState("deckBrowser")

    def _studyLinkHandler(self) -> None:
        # if overview already shown, switch to review
        if self.mw.state == "overview":
            self.mw.col.startTimebox()
            self.mw.moveToState("review")
        else:
            self.mw.onOverview()

    def _addLinkHandler(self) -> None:
        self.mw.onAddCard()

    def _browseLinkHandler(self) -> None:
        self.mw.onBrowse()

    def _statsLinkHandler(self) -> None:
        self.mw.onStats()

    def _syncLinkHandler(self) -> None:
        self.mw.on_sync_button_clicked()

    def _generateDeckLinkHandler(self) -> None:
        """Open Generate Deck dialog when toolbar button is clicked."""
        logger.debug("\n=== Generate Deck Handler Called ===")
        logger.debug("Creating dialog...")
        dialog = GenerateDeckDialog(self.mw)
        logger.debug("Showing dialog...")
        dialog.show()
        logger.debug("Dialog shown")

    def _aiSettingsLinkHandler(self) -> None:
        """Open AI Settings dialog when toolbar button is clicked."""
        logger.debug("\n=== AI Settings Handler Called ===")
        logger.debug("Creating dialog...")
        dialog = AISettingsDialog(self.mw)
        logger.debug("Showing dialog...")
        dialog.show()
        logger.debug("Dialog shown")

    # Add-ons
    ######################################################################

    def _left_tray_content(self) -> str:
        left_tray_content: list[str] = []
        gui_hooks.top_toolbar_will_set_left_tray_content(left_tray_content, self)
        return self._process_tray_content(left_tray_content)

    def _right_tray_content(self) -> str:
        right_tray_content: list[str] = []
        gui_hooks.top_toolbar_will_set_right_tray_content(right_tray_content, self)
        return self._process_tray_content(right_tray_content)

    def _process_tray_content(self, content: list[str]) -> str:
        return "\n".join(f"""<div class="tray-item">{item}</div>""" for item in content)

    # Sync
    ######################################################################

    def _create_sync_link(self) -> str:
        name = tr.qt_misc_sync()
        title = tr.actions_shortcut_key(val="Y")
        label = "sync"
        self.link_handlers[label] = self._syncLinkHandler

        return f"""
<a class=hitem tabindex="-1" aria-label="{name}" title="{title}" id="{label}" href=# onclick="return pycmd('{label}')"
>{name}<img id=sync-spinner src='/_anki/imgs/refresh.svg'>
</a>"""

    def set_sync_active(self, active: bool) -> None:
        method = "add" if active else "remove"
        self.web.eval(
            f"document.getElementById('sync-spinner').classList.{method}('spin')"
        )

    def set_sync_status(self, status: SyncStatus) -> None:
        self.web.eval(f"updateSyncColor({status.required})")

    def update_sync_status(self) -> None:
        get_sync_status(self.mw, self.mw.toolbar.set_sync_status)

    # HTML & CSS
    ######################################################################

    _body = """
<div id="header">
  <div class="header">
    <div class="left-tray">{left_tray_content}</div>
    <div class="toolbar">{toolbar_content}</div>
    <div class="right-tray">{right_tray_content}</div>
  </div>
</div>
"""


# Bottom bar
######################################################################


class BottomBar(Toolbar):
    _centerBody = """
<center id=outer><table width=100%% id=header><tr><td align=center>
%s</td></tr></table></center>
"""

    def draw(
        self,
        buf: str = "",
        web_context: Any | None = None,
        link_handler: Callable[[str], Any] | None = None,
    ) -> None:
        # note: some screens may override this
        web_context = web_context or BottomToolbar(self)
        link_handler = link_handler or self._linkHandler
        self.web.set_bridge_command(link_handler, web_context)
        self.web.stdHtml(
            self._centerBody % buf,
            css=["css/toolbar.css", "css/toolbar-bottom.css"],
            context=web_context,
        )
        self.web.adjustHeightToFit()
