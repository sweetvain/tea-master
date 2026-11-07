from . import admin, auth, friends, main, profile

BLUEPRINTS = (auth.bp, main.bp, profile.bp, friends.bp, admin.bp)
