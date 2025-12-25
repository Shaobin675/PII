LLM-Powered PII Detection Platform (Ongoing Project)
Overview

This project is an LLM-powered PII (Personally Identifiable Information) detection platform designed to identify and prevent sensitive data from leaving controlled boundaries. It targets logs, traces, PDFs, images, and knowledge-base text and is architected for enterprise-scale throughput while supporting HIPAA and similar regulatory compliance requirements.

The system is to be built with a microservices architecture, designed to scale horizontally and handle:

Individual documents larger than 100MB

Hundreds of millions of documents overall

High-throughput, I/O-bound workloads

The platform combines deterministic detection, ML-based NLP, and LLM-assisted reasoning to maximize accuracy while maintaining performance and explainability.

Key Capabilities

PII detection in: Plain text (logs, traces, KB articles), PDFs (text-based and scanned), Images (OCR-based) - completed

HIPAA-focused entity detection (PHI, identifiers, quasi-identifiers) - completed

Streaming and batch processing - working on it

Microservice-based isolation of responsibilities - working on it

Designed for Kubernetes-native deployment - working on it

Kafka-based ingestion and backpressure control - working on it
