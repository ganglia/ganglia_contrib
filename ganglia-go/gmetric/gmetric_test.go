package gmetric_test

import (
	"fmt"
	"strings"
	"testing"
	"time"

	"github.com/ganglia/ganglia_contrib/ganglia-go/gmetric"
	"github.com/ganglia/ganglia_contrib/ganglia-go/gmon"
	"github.com/ganglia/ganglia_contrib/ganglia-go/gmondtest"
)

func errContains(t *testing.T, err error, str string) {
	if err == nil {
		t.Fatalf(`was expecting error with "%s" but got nil error`, str)
	}
	if !strings.Contains(err.Error(), str) {
		t.Fatalf(`was expecting error with "%s" but got "%s"`, str, err.Error())
	}
}

func TestUint8Metric(t *testing.T) {
	t.Parallel()
	h := gmondtest.NewHarness(t)
	defer h.Stop()

	m := &gmetric.Metric{
		Name:         "uint8_metric",
		Host:         "localhost",
		ValueType:    gmetric.ValueUint8,
		Units:        "count",
		Slope:        gmetric.SlopeBoth,
		TickInterval: 20 * time.Second,
		Lifetime:     24 * time.Hour,
	}
	const val = 10

	if err := h.Client.WriteMeta(m); err != nil {
		t.Fatal(err)
	}

	if err := h.Client.WriteValue(m, val); err != nil {
		t.Fatal(err)
	}

	h.ContainsMetric(&gmon.Metric{
		Name:  m.Name,
		Value: fmt.Sprint(val),
		Unit:  m.Units,
		Tn:    1,
		Tmax:  20,
		Slope: "both",
	})
}

func TestUint32Metric(t *testing.T) {
	t.Parallel()
	h := gmondtest.NewHarness(t)
	defer h.Stop()

	m := &gmetric.Metric{
		Name:         "uint32_metric",
		Host:         "localhost",
		ValueType:    gmetric.ValueUint32,
		Units:        "count",
		Slope:        gmetric.SlopeBoth,
		TickInterval: 20 * time.Second,
		Lifetime:     24 * time.Hour,
	}
	const val = 10

	if err := h.Client.WriteMeta(m); err != nil {
		t.Fatal(err)
	}

	if err := h.Client.WriteValue(m, val); err != nil {
		t.Fatal(err)
	}

	h.ContainsMetric(&gmon.Metric{
		Name:  m.Name,
		Value: fmt.Sprint(val),
		Unit:  m.Units,
		Tn:    1,
		Tmax:  20,
		Slope: "both",
	})
}

func TestStringMetric(t *testing.T) {
	t.Parallel()
	h := gmondtest.NewHarness(t)
	defer h.Stop()

	m := &gmetric.Metric{
		Name:         "string_metric",
		Host:         "localhost",
		ValueType:    gmetric.ValueString,
		Units:        "count",
		Slope:        gmetric.SlopeBoth,
		TickInterval: 20 * time.Second,
		Lifetime:     24 * time.Hour,
	}
	const val = "hello"

	if err := h.Client.WriteMeta(m); err != nil {
		t.Fatal(err)
	}

	if err := h.Client.WriteValue(m, val); err != nil {
		t.Fatal(err)
	}

	h.ContainsMetric(&gmon.Metric{
		Name:  m.Name,
		Unit:  m.Units,
		Value: val,
		Tn:    1,
		Tmax:  20,
		Slope: "both",
	})
}

func TestFloatMetric(t *testing.T) {
	t.Parallel()
	h := gmondtest.NewHarness(t)
	defer h.Stop()

	m := &gmetric.Metric{
		Name:         "float_metric",
		Host:         "localhost",
		ValueType:    gmetric.ValueFloat32,
		Units:        "count",
		Slope:        gmetric.SlopeBoth,
		TickInterval: 20 * time.Second,
		Lifetime:     24 * time.Hour,
	}
	const val = 3.14

	if err := h.Client.WriteMeta(m); err != nil {
		t.Fatal(err)
	}

	if err := h.Client.WriteValue(m, val); err != nil {
		t.Fatal(err)
	}

	h.ContainsMetric(&gmon.Metric{
		Name:  m.Name,
		Unit:  m.Units,
		Value: fmt.Sprint(val),
		Tn:    1,
		Tmax:  20,
		Slope: "both",
	})
}

func TestExtras(t *testing.T) {
	t.Parallel()
	h := gmondtest.NewHarness(t)
	defer h.Stop()

	m := &gmetric.Metric{
		Name:         "extras_metric",
		Spoof:        "127.0.0.1:localhost_spoof",
		Title:        "the simple title",
		Description:  "the simple description",
		Host:         "localhost",
		Groups:       []string{"simple_group1", "simple_group2"},
		ValueType:    gmetric.ValueString,
		Units:        "count",
		Slope:        gmetric.SlopeBoth,
		TickInterval: 20 * time.Second,
		Lifetime:     24 * time.Hour,
	}
	const val = "hello"

	if err := h.Client.WriteMeta(m); err != nil {
		t.Fatal(err)
	}

	if err := h.Client.WriteValue(m, val); err != nil {
		t.Fatal(err)
	}

	h.ContainsMetric(&gmon.Metric{
		Name:  m.Name,
		Unit:  m.Units,
		Value: val,
		Tn:    1,
		Tmax:  20,
		Slope: "both",
		ExtraData: gmon.ExtraData{
			ExtraElements: []gmon.ExtraElement{
				gmon.ExtraElement{Name: "GROUP", Val: m.Groups[1]},
				gmon.ExtraElement{Name: "GROUP", Val: m.Groups[0]},
				gmon.ExtraElement{Name: "SPOOF_HOST", Val: m.Spoof},
				gmon.ExtraElement{Name: "DESC", Val: m.Description},
				gmon.ExtraElement{Name: "TITLE", Val: m.Title},
			},
		},
	})
}

func TestNoAddrs(t *testing.T) {
	t.Parallel()
	c := &gmetric.Client{}
	errContains(t, c.Open(), "gmetric: no addrs provided")
	errContains(t, c.Close(), "gmetric: no addrs provided")
}

func TestNotOpen(t *testing.T) {
	t.Parallel()
	c := &gmetric.Client{}
	m := &gmetric.Metric{
		Name:      "string_metric",
		Host:      "localhost",
		ValueType: gmetric.ValueString,
	}
	errContains(t, c.WriteMeta(m), "gmetric: client not opened")
	errContains(t, c.WriteValue(m, "val"), "gmetric: client not opened")
}

func TestLifetimeFromClient(t *testing.T) {
	t.Parallel()
	h := gmondtest.NewHarness(t)
	h.Client.Lifetime = 24 * time.Hour
	defer h.Stop()

	m := &gmetric.Metric{
		Name:         "lifetime_from_client_metric",
		Host:         "localhost",
		ValueType:    gmetric.ValueUint8,
		Units:        "count",
		Slope:        gmetric.SlopeBoth,
		TickInterval: 20 * time.Second,
	}
	const val = 10

	if err := h.Client.WriteMeta(m); err != nil {
		t.Fatal(err)
	}

	if err := h.Client.WriteValue(m, val); err != nil {
		t.Fatal(err)
	}

	h.ContainsMetric(&gmon.Metric{
		Name:  m.Name,
		Value: fmt.Sprint(val),
		Unit:  m.Units,
		Tn:    1,
		Tmax:  20,
		Slope: "both",
	})
}

func TestTickIntervalFromClient(t *testing.T) {
	t.Parallel()
	h := gmondtest.NewHarness(t)
	h.Client.TickInterval = 20 * time.Second
	defer h.Stop()

	m := &gmetric.Metric{
		Name:      "tick_interval_from_client_metric",
		Host:      "localhost",
		ValueType: gmetric.ValueUint8,
		Units:     "count",
		Slope:     gmetric.SlopeBoth,
		Lifetime:  24 * time.Hour,
	}
	const val = 10

	if err := h.Client.WriteMeta(m); err != nil {
		t.Fatal(err)
	}

	if err := h.Client.WriteValue(m, val); err != nil {
		t.Fatal(err)
	}

	h.ContainsMetric(&gmon.Metric{
		Name:  m.Name,
		Value: fmt.Sprint(val),
		Unit:  m.Units,
		Tn:    1,
		Tmax:  20,
		Slope: "both",
	})
}

func TestHostnameFromClient(t *testing.T) {
	t.Parallel()
	h := gmondtest.NewHarness(t)
	h.Client.Host = "localhost"
	defer h.Stop()

	m := &gmetric.Metric{
		Name:         "hostname_from_client_metric",
		ValueType:    gmetric.ValueUint8,
		Units:        "count",
		Slope:        gmetric.SlopeBoth,
		TickInterval: 20 * time.Second,
		Lifetime:     24 * time.Hour,
	}
	const val = 10

	if err := h.Client.WriteMeta(m); err != nil {
		t.Fatal(err)
	}

	if err := h.Client.WriteValue(m, val); err != nil {
		t.Fatal(err)
	}

	h.ContainsMetric(&gmon.Metric{
		Name:  m.Name,
		Value: fmt.Sprint(val),
		Unit:  m.Units,
		Tn:    1,
		Tmax:  20,
		Slope: "both",
	})
}

func TestSpoofFromClient(t *testing.T) {
	t.Parallel()
	h := gmondtest.NewHarness(t)
	h.Client.Spoof = "127.0.0.1:localhost_spoof"
	defer h.Stop()

	m := &gmetric.Metric{
		Name:         "spoof_from_client_metric",
		Host:         "localhost",
		ValueType:    gmetric.ValueString,
		Units:        "count",
		Slope:        gmetric.SlopeBoth,
		TickInterval: 20 * time.Second,
		Lifetime:     24 * time.Hour,
	}
	const val = "hello"

	if err := h.Client.WriteMeta(m); err != nil {
		t.Fatal(err)
	}

	if err := h.Client.WriteValue(m, val); err != nil {
		t.Fatal(err)
	}

	h.ContainsMetric(&gmon.Metric{
		Name:  m.Name,
		Unit:  m.Units,
		Value: val,
		Tn:    1,
		Tmax:  20,
		Slope: "both",
		ExtraData: gmon.ExtraData{
			ExtraElements: []gmon.ExtraElement{
				gmon.ExtraElement{Name: "SPOOF_HOST", Val: h.Client.Spoof},
			},
		},
	})
}

func TestNoName(t *testing.T) {
	t.Parallel()
	h := gmondtest.NewHarness(t)
	defer h.Stop()

	m := &gmetric.Metric{}
	errContains(t, h.Client.WriteMeta(m), "gmetric: metric has no name")
	errContains(t, h.Client.WriteValue(m, "val"), "gmetric: metric has no name")
}

func TestNoValueType(t *testing.T) {
	t.Parallel()
	h := gmondtest.NewHarness(t)
	defer h.Stop()

	m := &gmetric.Metric{
		Name: "no_value_type_metric",
	}
	errContains(t, h.Client.WriteMeta(m), "gmetric: metric has no ValueType")
	errContains(t, h.Client.WriteValue(m, "val"), "gmetric: metric has no ValueType")
}
