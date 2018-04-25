DROP TABLE IF EXISTS `fingerprints`;

/*!40101 SET @saved_cs_client     = @@character_set_client */;

/*!40101 SET character_set_client = utf8 */;

CREATE TABLE `fingerprints` (

  `id` bigint(20) NOT NULL AUTO_INCREMENT,

  `navigator.userAgent` text,

  `navigator.platform` text,

  `navigator.vendor` text,

  `navigator.productSub` text,

  `navigator.languages` text,

  `httpHeader.accept` text,

  `httpHeader.accept_language` text,

  `httpHeader.accept_encoding` text,

  `navigator.plugins` text,

  `navigator.mimeTypes` text,

  `navigator.cookieEnabled` tinyint(4) DEFAULT NULL,

  `screen.colorDepth` int(11) DEFAULT NULL,

  `screen.pixelDepth` int(11) DEFAULT NULL,

  `screen.width` int(11) DEFAULT NULL,

  `screen.availWidth` int(11) DEFAULT NULL,

  `screen.height` int(11) DEFAULT NULL,

  `screen.availHeight` int(11) DEFAULT NULL,

  `timezoneOffset` int(11) DEFAULT NULL,

  `navigator.language` text,

  PRIMARY KEY (`id`)

) ENGINE=InnoDB AUTO_INCREMENT=80 DEFAULT CHARSET=latin1;