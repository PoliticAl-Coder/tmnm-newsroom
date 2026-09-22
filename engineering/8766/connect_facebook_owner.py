"""One-click owner controller. Browser opening is dependency-injected for non-live validation."""
from __future__ import annotations
import http.server, threading, webbrowser
from meta_connect import OAuthGuard, REDIRECT_URI
class ConnectFacebookOwnerAction:
 def __init__(self,browser_open=webbrowser.open): self.browser_open=browser_open; self.guard=OAuthGuard()
 def start(self,open_browser=True):
  url=self.guard.begin()
  if open_browser:self.browser_open(url)
  return {"status":"BROWSER_BOUNDARY_READY","facebook_write":0}
# Real callback listener/token exchange is deliberately not invoked during preparation.
