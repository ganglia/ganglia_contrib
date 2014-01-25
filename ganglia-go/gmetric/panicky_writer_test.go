package gmetric

import (
	"errors"
	"testing"
	"time"
)

var errFixed = errors.New("fixed error")

type errWriter int

func (e errWriter) Write(b []byte) (int, error) {
	return 0, errFixed
}

var panicFixed = "foo42"

type panicWriter int

func (e panicWriter) Write(b []byte) (int, error) {
	panic(panicFixed)
}

func TestWriteMetaWriterError(t *testing.T) {
	t.Parallel()
	c := &Client{}
	m := &Metric{
		Name:         "write_meta_panic_metric",
		Host:         "localhost",
		ValueType:    ValueUint32,
		Units:        "count",
		Slope:        SlopeBoth,
		TickInterval: 20 * time.Second,
		Lifetime:     24 * time.Hour,
	}
	if err := m.writeMeta(c, errWriter(0)); err != errFixed {
		t.Fatalf("was expecting errFixed but got %s", err)
	}
}

func TestWriteValueWriterError(t *testing.T) {
	t.Parallel()
	c := &Client{}
	m := &Metric{
		Name:         "string_metric",
		Host:         "localhost",
		ValueType:    ValueString,
		Units:        "count",
		Slope:        SlopeBoth,
		TickInterval: 20 * time.Second,
		Lifetime:     24 * time.Hour,
	}
	if err := m.writeValue(c, errWriter(0), "val"); err != errFixed {
		t.Fatalf("was expecting errFixed but got %s", err)
	}
}

func TestWriteMetaWriterPanic(t *testing.T) {
	t.Parallel()
	c := &Client{}
	defer func() {
		if r := recover(); r != panicFixed {
			t.Fatalf("was expecting panicFixed but got %s", r)
		}
	}()
	m := &Metric{
		Name:         "write_meta_panic_metric",
		Host:         "localhost",
		ValueType:    ValueUint32,
		Units:        "count",
		Slope:        SlopeBoth,
		TickInterval: 20 * time.Second,
		Lifetime:     24 * time.Hour,
	}
	if err := m.writeMeta(c, panicWriter(0)); err != errFixed {
		t.Fatalf("was expecting errFixed but got %s", err)
	}
}

func TestWriteValueWriterPanic(t *testing.T) {
	t.Parallel()
	c := &Client{}
	defer func() {
		if r := recover(); r != panicFixed {
			t.Fatalf("was expecting panicFixed but got %s", r)
		}
	}()
	m := &Metric{
		Name:         "string_metric",
		Host:         "localhost",
		ValueType:    ValueString,
		Units:        "count",
		Slope:        SlopeBoth,
		TickInterval: 20 * time.Second,
		Lifetime:     24 * time.Hour,
	}
	if err := m.writeValue(c, panicWriter(0), "val"); err != errFixed {
		t.Fatalf("was expecting errFixed but got %s", err)
	}
}
