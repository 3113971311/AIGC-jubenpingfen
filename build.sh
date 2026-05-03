#!/bin/bash
set -e

cd backend && pip install -r requirements.txt
cd ../frontend && pnpm install && pnpm run build
