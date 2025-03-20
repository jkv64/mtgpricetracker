CREATE DATABASE IF NOT EXISTS mtgpricetracker;

USE mtgpricetracker;

DROP TABLE IF EXISTS prices;
DROP TABLE IF EXISTS cards;

-- this table just tracks which cards should be updated by the scheduled update function
-- dateadded is used by the price checking method to handle when people give dates too far in the past 

CREATE TABLE cards
(
    cardid       int not null AUTO_INCREMENT,
    cardname     varchar(256) not null,
    dateadded    date not null,
    PRIMARY KEY  (cardid)
);

ALTER TABLE cards AUTO_INCREMENT = 10001;  -- starting value

-- this table holds the daily price entries created by the fetch_prices method
-- cardid should be the foreign key for cards, but I did not realize I would need two tables
-- before I started tracking prices, and I didn't want to start over... oops

CREATE TABLE prices
(
    priceid      int not null AUTO_INCREMENT,
    setcode      varchar(8) not null,
    price        float not null,
    cardname     varchar(256) not null,
    pricedate    date not null,
    imagekey     varchar(256) not null,
    PRIMARY KEY  (priceid)
);


ALTER TABLE prices AUTO_INCREMENT = 1001;  -- starting value


--
-- This is creating user accounts for database access. You can change the details
--
-- ref: https://dev.mysql.com/doc/refman/8.0/en/create-user.html
--


DROP USER IF EXISTS 'mtgpricetracker-read-only';
DROP USER IF EXISTS 'mtgpricetracker-read-write';


CREATE USER 'mtgpricetracker-read-only' IDENTIFIED BY 'aridmesa12!';
CREATE USER 'mtgpricetracker-read-write' IDENTIFIED BY 'marshflats34!';


GRANT SELECT, SHOW VIEW ON mtgpricetracker.* 
      TO 'mtgpricetracker-read-only';
GRANT SELECT, SHOW VIEW, INSERT, UPDATE, DELETE, DROP, CREATE, ALTER ON mtgpricetracker.* 
      TO 'mtgpricetracker-read-write';
      
FLUSH PRIVILEGES;
