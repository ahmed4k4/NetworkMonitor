class GeoIPService:

    def lookup(self, ip):

        # سيتم ربط GeoIP database
        # في مرحلة لاحقة.

        return {
            "ip": ip,
            "country": None,
            "asn": None,
            "organization": None,
        }