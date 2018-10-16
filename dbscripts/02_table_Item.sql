CREATE TABLE `Item` (
  `ItemId` int(11) NOT NULL AUTO_INCREMENT,
  `Description` varchar(200) CHARACTER SET latin1 DEFAULT NULL,
  `Price` int(11) DEFAULT NULL,
  `Date` datetime DEFAULT NULL,
  `ImageURL` varchar(145) CHARACTER SET latin1 DEFAULT NULL,
  `ToriURL` varchar(145) CHARACTER SET latin1 DEFAULT NULL,
  `ToriId` int(11) DEFAULT NULL,
  `Category` varchar(145) CHARACTER SET latin1 DEFAULT NULL,
  `Location` varchar(45) CHARACTER SET latin1 DEFAULT NULL,
  PRIMARY KEY (`ItemId`)
) ENGINE=InnoDB AUTO_INCREMENT=1434112 DEFAULT CHARSET=utf8;

