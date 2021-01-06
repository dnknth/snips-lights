BIN = $(PWD)/.venv3/bin
GETTEXT = /usr/local/opt/gettext

POT = locale/messages.pot
LOCALE = locale/de/LC_MESSAGES/messages.po
SOURCES = $(wildcard *.py)
MAIN = $(wildcard action-*.py)

run: .venv3 $(POT) $(LOCALE:.po=.mo)
	$(BIN)/python3 $(MAIN) -v3

.venv3: requirements.txt
	[ -d $@ ] || python3 -m .venv3 $@
	ln -sf $@ venv
	$(BIN)/pip3 install -U pip
	$(BIN)/pip3 install wheel
	$(BIN)/pip3 install -r $<
	touch $@

test: tests
	$(BIN)/python3 -m snips_skill.test tests/*

tests:
	mkdir -p tests
	$(BIN)/python3 -m snips_skill.test -d tests -l
	
log:
	$(BIN)/python3 -m snips_skill
	
messages: $(POT)

$(POT): $(SOURCES)
	mkdir -p locale
	$(GETTEXT)/bin/xgettext -L python -o $@ $^

%.mo: %.po
	$(GETTEXT)/bin/msgfmt -o $@ $<

clean:
	rm -rf __pycache__

tidy: clean
	rm -rf venv tests
