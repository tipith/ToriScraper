CREATE TABLE `ItemAlarm` (
  `ItemAlarmId` int(11) NOT NULL AUTO_INCREMENT,
  `Description` varchar(200) DEFAULT NULL,
  `Price` int(11) DEFAULT NULL,
  `Date` datetime DEFAULT NULL,
  `ImageURL` varchar(145) DEFAULT NULL,
  `ToriURL` varchar(145) DEFAULT NULL,
  `ToriId` int(11) DEFAULT NULL,
  `Category` varchar(145) DEFAULT NULL,
  `Location` varchar(45) DEFAULT NULL,
  `UserId` int(11) DEFAULT NULL,
  PRIMARY KEY (`ItemAlarmId`),
  KEY `fk_itemalarm_user_idx` (`UserId`),
  CONSTRAINT `fk_itemalarm_user` FOREIGN KEY (`UserId`) REFERENCES `User` (`userId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB AUTO_INCREMENT=2126 DEFAULT CHARSET=utf8