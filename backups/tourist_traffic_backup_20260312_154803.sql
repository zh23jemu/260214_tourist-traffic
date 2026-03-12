-- MySQL dump 10.13  Distrib 8.4.8, for Linux (x86_64)
--
-- Host: localhost    Database: tourist_traffic
-- ------------------------------------------------------
-- Server version	8.4.8

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `clean_flow_daily`
--

DROP TABLE IF EXISTS `clean_flow_daily`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `clean_flow_daily` (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL,
  `province` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `county` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `predicted_count_raw` int DEFAULT NULL,
  `actual_count` int NOT NULL,
  `weather_text` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `weather_type` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `temp_c` float DEFAULT NULL,
  `weekday_text` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `day_type` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `prediction_generated_time` datetime DEFAULT NULL,
  `prediction_bias_raw` float DEFAULT NULL,
  `quality_flag` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `source_batch_id` int NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_clean_date_county` (`date`,`county`),
  KEY `source_batch_id` (`source_batch_id`),
  KEY `ix_clean_flow_daily_date` (`date`),
  KEY `ix_clean_flow_daily_county` (`county`),
  KEY `ix_clean_flow_daily_id` (`id`),
  CONSTRAINT `clean_flow_daily_ibfk_1` FOREIGN KEY (`source_batch_id`) REFERENCES `import_batch` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `clean_flow_daily`
--

LOCK TABLES `clean_flow_daily` WRITE;
/*!40000 ALTER TABLE `clean_flow_daily` DISABLE KEYS */;
/*!40000 ALTER TABLE `clean_flow_daily` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `feature_daily`
--

DROP TABLE IF EXISTS `feature_daily`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `feature_daily` (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL,
  `county` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `feature_version` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `actual_count` int DEFAULT NULL,
  `day_of_week` int NOT NULL,
  `month` int NOT NULL,
  `is_weekend` int NOT NULL,
  `is_holiday_proxy` int NOT NULL,
  `temp_c` float NOT NULL,
  `weather_type_code` int NOT NULL,
  `lag_1` float DEFAULT NULL,
  `lag_7` float DEFAULT NULL,
  `lag_14` float DEFAULT NULL,
  `rolling_mean_7` float DEFAULT NULL,
  `rolling_std_7` float DEFAULT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_feature_key` (`date`,`county`,`feature_version`),
  KEY `ix_feature_daily_county` (`county`),
  KEY `ix_feature_daily_feature_version` (`feature_version`),
  KEY `ix_feature_daily_date` (`date`),
  KEY `ix_feature_daily_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `feature_daily`
--

LOCK TABLES `feature_daily` WRITE;
/*!40000 ALTER TABLE `feature_daily` DISABLE KEYS */;
/*!40000 ALTER TABLE `feature_daily` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `import_batch`
--

DROP TABLE IF EXISTS `import_batch`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `import_batch` (
  `id` int NOT NULL AUTO_INCREMENT,
  `filename` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `total_rows` int NOT NULL,
  `success_rows` int NOT NULL,
  `error_rows` int NOT NULL,
  `error_summary` text COLLATE utf8mb4_unicode_ci,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_import_batch_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `import_batch`
--

LOCK TABLES `import_batch` WRITE;
/*!40000 ALTER TABLE `import_batch` DISABLE KEYS */;
/*!40000 ALTER TABLE `import_batch` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `model_registry`
--

DROP TABLE IF EXISTS `model_registry`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `model_registry` (
  `model_version` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `county` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `feature_version` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `horizon` int NOT NULL,
  `algorithm` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `metrics_json` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `train_start` date NOT NULL,
  `train_end` date NOT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`model_version`),
  KEY `ix_model_registry_feature_version` (`feature_version`),
  KEY `ix_model_registry_county` (`county`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `model_registry`
--

LOCK TABLES `model_registry` WRITE;
/*!40000 ALTER TABLE `model_registry` DISABLE KEYS */;
/*!40000 ALTER TABLE `model_registry` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `prediction_daily`
--

DROP TABLE IF EXISTS `prediction_daily`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `prediction_daily` (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL,
  `county` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `horizon` int NOT NULL,
  `model_version` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `y_pred` float NOT NULL,
  `y_low` float NOT NULL,
  `y_high` float NOT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_prediction_key` (`date`,`county`,`horizon`,`model_version`),
  KEY `ix_prediction_daily_model_version` (`model_version`),
  KEY `ix_prediction_daily_id` (`id`),
  KEY `ix_prediction_daily_county` (`county`),
  KEY `ix_prediction_daily_date` (`date`),
  CONSTRAINT `prediction_daily_ibfk_1` FOREIGN KEY (`model_version`) REFERENCES `model_registry` (`model_version`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `prediction_daily`
--

LOCK TABLES `prediction_daily` WRITE;
/*!40000 ALTER TABLE `prediction_daily` DISABLE KEYS */;
/*!40000 ALTER TABLE `prediction_daily` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `raw_flow_daily`
--

DROP TABLE IF EXISTS `raw_flow_daily`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `raw_flow_daily` (
  `id` int NOT NULL AUTO_INCREMENT,
  `batch_id` int NOT NULL,
  `row_number` int NOT NULL,
  `raw_date` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `raw_province` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `raw_county` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `raw_predicted_count` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `raw_actual_count` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `raw_weather` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `raw_weekday` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `raw_day_type` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `raw_prediction_time` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `raw_bias` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `error_message` text COLLATE utf8mb4_unicode_ci,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_raw_flow_daily_batch_id` (`batch_id`),
  KEY `ix_raw_flow_daily_id` (`id`),
  CONSTRAINT `raw_flow_daily_ibfk_1` FOREIGN KEY (`batch_id`) REFERENCES `import_batch` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `raw_flow_daily`
--

LOCK TABLES `raw_flow_daily` WRITE;
/*!40000 ALTER TABLE `raw_flow_daily` DISABLE KEYS */;
/*!40000 ALTER TABLE `raw_flow_daily` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_account`
--

DROP TABLE IF EXISTS `user_account`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_account` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `role` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_user_account_username` (`username`),
  KEY `ix_user_account_id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_account`
--

LOCK TABLES `user_account` WRITE;
/*!40000 ALTER TABLE `user_account` DISABLE KEYS */;
INSERT INTO `user_account` VALUES (1,'admin','H0n0ijy4hyWsz7URKRY7Uw==$JN5c95v+97DD4QypvaGYRytGw+Aa+Gi/jK0esN8cA8s=','admin',1,'2026-03-08 03:10:08','2026-03-08 03:10:08');
/*!40000 ALTER TABLE `user_account` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-03-12  7:48:03
