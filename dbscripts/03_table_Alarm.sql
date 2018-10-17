CREATE TABLE `Alarm` (
  `AlarmId` int(11) NOT NULL AUTO_INCREMENT,
  `SearchPattern` varchar(100) DEFAULT NULL,
  `MaxPrice` int(11) DEFAULT NULL,
  `MinPrice` int(11) DEFAULT NULL,
  `UserId` int(11) DEFAULT NULL,
  `Location` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`AlarmId`),
  KEY `fk_alarm_user_idx` (`UserId`),
  CONSTRAINT `fk_alarm_user` FOREIGN KEY (`UserId`) REFERENCES `User` (`userId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8