package gmetric_test

import (
	"fmt"
	"net"
	"os"
	"time"

	"github.com/ganglia/ganglia_contrib/ganglia-go/gmetric"
)

func Example() {
	// A Client can connect to multiple addresses.
	client := &gmetric.Client{
		Addr: []net.Addr{
			&net.UDPAddr{IP: net.ParseIP("127.0.0.1"), Port: 8649},
		},
	}

	// You only need to Open the connections once on application startup.
	if err := client.Open(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}

	// Defines the Metric.
	metric := &gmetric.Metric{
		Name:         "web_requests",
		Title:        "Number of Web Requests",
		Host:         "web0.app.com",
		ValueType:    gmetric.ValueUint32,
		Units:        "count",
		Slope:        gmetric.SlopeBoth,
		TickInterval: 20 * time.Second,
		Lifetime:     24 * time.Hour,
	}

	// Meta packets only need to be sent every `send_metadata_interval` as
	// configured in gmond.conf.
	if err := client.WriteMeta(metric); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}

	if err := client.WriteValue(metric, 1); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}

	// Close the connections before terminating your application.
	if err := client.Close(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
