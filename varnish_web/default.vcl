# Specify a backend e.g. your Apache server running Ganglia
backend default {
    .host = "127.0.0.1";
    .port = "8080";
    .first_byte_timeout = 60s;
}

sub vcl_recv {
  # We are exposing Ganglia via varnish as /ganglia3/. So we need to rewrite
  # the URL we send to the backend since Ganglia lives under /ganglia2 
  if (req.url ~ "^/ganglia3") {
    set req.url = regsub(req.url, "^/ganglia3", "/ganglia2");
  }
  return (lookup);
}

sub vcl_fetch {

   # Front page can be cached for 20 minutes. Cluster list shouldn't 
   # change that often
   if (req.url ~ "^/(ganglia2/)?$" ) {
     set beresp.ttl = 1200s;
     unset beresp.http.Cache-Control;
     unset beresp.http.Expires;
     unset beresp.http.Pragma;
     unset beresp.http.Set-Cookie;
   }

   # Cache CSS and JS for a day
   if (req.url ~ "^/(ganglia2/)?(css|js)" || req.url ~ "^/naglite3(.*)\.(css|js)$" ) {
     set beresp.ttl = 86400s;
     unset beresp.http.Expires;
     unset beresp.http.Pragma;
     unset beresp.http.Set-Cookie;
     set beresp.http.Cache-Control = "public, max-age=86400";
   }

   # By default cache all graphs for 30 seconds however tell the browser to cache it for 15 seconds
   if (req.url ~ "/(ganglia2/)?graph.php") {
     set beresp.ttl = 15s;
     set beresp.http.Cache-Control = "public, max-age=15";
     unset beresp.http.Pragma;
     unset beresp.http.Expires;
     unset beresp.http.Set-Cookie;
   }

   # Yearly graphs show day averages so no need to regenerate that all the time
   # Cache for a day. Monthly graphs cache for 2 hours and daily graphs for 5 minutes
   if (req.url ~ "/(ganglia2/)?graph.php\?(.*)r=year") {
     set beresp.ttl = 86400s;
     set beresp.http.Cache-Control = "public, max-age=86400s";
   } else if ( req.url ~ "/(ganglia2/)?graph.php\?(.*)r=month") {
     set beresp.ttl = 7200s;
     set beresp.http.Cache-Control = "public, max-age=7200s";
   } else if ( req.url ~ "/(ganglia2/)?graph.php\?(.*)r=day") {
     set beresp.ttl = 300s;
     set beresp.http.Cache-Control = "public, max-age=300s";
   } else if ( req.url ~ "/(ganglia2/)?graph.php\?(.*)r=4hr") {
     set beresp.ttl = 60s;
     set beresp.http.Cache-Control = "public, max-age=60s";
   } else if ( req.url ~ "^/(ganglia2/)?\?.*vn=(.*)&" ) {
     set beresp.ttl = 300s;
     set beresp.http.Cache-Control = "public, max-age=300s";
   } else if ( req.url ~ "^/(ganglia2/)?autorotation.php" ) {
     set beresp.ttl = 900s;
     set beresp.http.Cache-Control = "public, max-age=300s";
   }

   # Graph All periods can be cached for a long time
   if (req.url ~ "/(ganglia2/)?graph_all_periods.php") {
     set beresp.ttl = 86400s;
     set beresp.http.Cache-Control = "public, max-age=600";
     unset beresp.http.Pragma;
     unset beresp.http.Expires;
     unset beresp.http.Set-Cookie;
   }
   
   return (deliver);
}

sub vcl_deliver {
  if (obj.hits > 0) {
    set resp.http.X-Cache = "HIT";
    set resp.http.X-Cache-Hits = obj.hits;
  } else {
    set resp.http.X-Cache = "MISS";
  }
}
