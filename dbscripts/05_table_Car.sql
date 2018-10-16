CREATE TABLE `Car` (
  `ItemId` int(11) NOT NULL AUTO_INCREMENT,
  `Description` varchar(200) CHARACTER SET latin1 DEFAULT NULL,
  `Price` int(11) DEFAULT NULL,
  `Date` datetime DEFAULT NULL,
  `ImageURL` varchar(145) CHARACTER SET latin1 DEFAULT NULL,

  `ToriURL` varchar(145) CHARACTER SET latin1 DEFAULT NULL,
  `ToriId` int(11) DEFAULT NULL,
  `Category` varchar(145) CHARACTER SET latin1 DEFAULT NULL,
  `Location` varchar(45) CHARACTER SET latin1 DEFAULT NULL,
  `car_ac` int DEFAULT NULL,

  `car_cruise` int DEFAULT NULL,
  `car_engine_heater` int DEFAULT NULL,
  `car_hook` int DEFAULT NULL,
  `car_fuel_expense` int(11) DEFAULT NULL,
  `car_tax` int(11) DEFAULT NULL,

  `car_year` int(11) DEFAULT NULL,
  `car_odo` int(11) DEFAULT NULL,
  `car_fuel_type` varchar(45) CHARACTER SET latin1 DEFAULT NULL,
  `car_gear` varchar(45) CHARACTER SET latin1 DEFAULT NULL,
  `car_plate` varchar(45) CHARACTER SET latin1 DEFAULT NULL,
  `car_type` varchar(45) CHARACTER SET latin1 DEFAULT NULL,

  `car_description_extra` varchar(1000) CHARACTER SET latin1 DEFAULT NULL,
  `car_info` varchar(10000) CHARACTER SET latin1 DEFAULT NULL,

  PRIMARY KEY (`ItemId`)
) ENGINE=InnoDB AUTO_INCREMENT=1434112 DEFAULT CHARSET=utf8;

