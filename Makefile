CONVERT = jupyter nbconvert --to html
SRCS1 = $(wildcard notes*.ipynb)
SRCS2 = $(wildcard ex*.ipynb)
SRCS3 = $(wildcard tick*.ipynb)
SRCS4 = $(wildcard extra*.ipynb)

%.html: %.ipynb
	$(CONVERT) $*

all: $(SRCS1:.ipynb=.html) $(SRCS2:.ipynb=.html) $(SRCS3:.ipynb=.html) $(SRCS4:.ipynb=.html)

