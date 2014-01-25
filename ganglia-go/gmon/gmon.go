// Package gmon provides read access to the gmon data.
package gmon

import (
	"bufio"
	"encoding/xml"
	"io"
	"net"

	"code.google.com/p/go-charset/charset"
	_ "code.google.com/p/go-charset/data"
)

type ExtraElement struct {
	Name string `xml:"NAME,attr"`
	Val  string `xml:"VAL,attr"`
}

type ExtraData struct {
	ExtraElements []ExtraElement `xml:"EXTRA_ELEMENT"`
}

type Metric struct {
	Name      string    `xml:"NAME,attr"`
	Value     string    `xml:"VAL,attr"`
	Unit      string    `xml:"UNITS,attr"`
	Slope     string    `xml:"SLOPE,attr"`
	Tn        int       `xml:"TN,attr"`
	Tmax      int       `xml:"TMAX,attr"`
	Dmax      int       `xml:"DMAX,attr"`
	ExtraData ExtraData `xml:"EXTRA_DATA"`
}

type Host struct {
	Name         string   `xml:"NAME,attr"`
	Ip           string   `xml:"IP,attr"`
	Tags         string   `xml:"TAGS,attr"`
	Reported     int      `xml:"REPORTED,attr"`
	Tn           int      `xml:"TN,attr"`
	Tmax         int      `xml:"TMAX,attr"`
	Dmax         int      `xml:"DMAX,attr"`
	Location     string   `xml:"LOCATION,attr"`
	GmondStarted int      `xml:"GMOND_STARTED,attr"`
	Metrics      []Metric `xml:"METRIC"`
}

type Cluster struct {
	Name      string `xml:"NAME,attr"`
	Owner     string `xml:"OWNER,attr"`
	LatLong   string `xml:"LATLONG,attr"`
	Url       string `xml:"URL,attr"`
	Localtime int    `xml:"LOCALTIME,attr"`
	Hosts     []Host `xml:"HOST"`
}

type Ganglia struct {
	XMLNAME  xml.Name  `xml:"GANGLIA_XML"`
	Clusters []Cluster `xml:"CLUSTER"`
}

// Read the gmond XML output.
func Read(r io.Reader) (*Ganglia, error) {
	ganglia := Ganglia{}
	decoder := xml.NewDecoder(r)
	decoder.CharsetReader = charset.NewReader
	if err := decoder.Decode(&ganglia); err != nil {
		return nil, err
	}
	return &ganglia, nil
}

// Connect to the given network/address and read from it.
func RemoteRead(network, addr string) (*Ganglia, error) {
	c, err := net.Dial(network, addr)
	if err != nil {
		return nil, err
	}
	defer c.Close()
	return Read(bufio.NewReader(c))
}
