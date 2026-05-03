#!/bin/bash
set -e

cd backend && uvicorn deploy_app:app --host :: --port 5000
