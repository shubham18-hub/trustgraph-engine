#!/bin/bash
# TrustGraph Engine - Restore Script
# Restores database and data from S3 backup

set -e

# Configuration
BACKUP_NAME="${1}"
S3_BUCKET="${S3_BACKUP_BUCKET:-trustgraph-backups-production}"
AWS_REGION="${AWS_REGION:-ap-south-1}"
RESTORE_DIR="/tmp/trustgraph-restore"

if [ -z "$BACKUP_NAME" ]; then
    echo "Usage: $0 <backup-name>"
    echo ""
    echo "Available backups:"
    aws s3 ls "s3://${S3_BUCKET}/" --region "$AWS_REGION" | grep ".tar.gz"
    exit 1
fi

echo "=========================================="
echo "TrustGraph Engine - Restore Script"
echo "=========================================="
echo "Backup: $BACKUP_NAME"
echo "S3 Bucket: $S3_BUCKET"
echo "Region: $AWS_REGION"
echo "=========================================="

# Create restore directory
mkdir -p "$RESTORE_DIR"

# Download backup from S3
echo "[1/4] Downloading backup from S3..."
aws s3 cp "s3://${S3_BUCKET}/${BACKUP_NAME}.tar.gz" "$RESTORE_DIR/${BACKUP_NAME}.tar.gz" \
    --region "$AWS_REGION"

if [ $? -ne 0 ]; then
    echo "✗ Failed to download backup from S3"
    exit 1
fi
echo "✓ Backup downloaded"

# Extract backup
echo "[2/4] Extracting backup..."
cd "$RESTORE_DIR"
tar -xzf "${BACKUP_NAME}.tar.gz"
echo "✓ Backup extracted"

# Display metadata
echo "[3/4] Backup metadata:"
if [ -f "$RESTORE_DIR/$BACKUP_NAME/metadata.json" ]; then
    cat "$RESTORE_DIR/$BACKUP_NAME/metadata.json"
fi

# Confirm restore
echo ""
read -p "Do you want to proceed with restore? This will overwrite existing data. (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled"
    rm -rf "$RESTORE_DIR"
    exit 0
fi

# Restore database
echo "[4/4] Restoring data..."
if [ -f "$RESTORE_DIR/$BACKUP_NAME/trustgraph.db" ]; then
    # Backup current database
    if [ -f "/app/data/trustgraph.db" ]; then
        mv /app/data/trustgraph.db "/app/data/trustgraph.db.backup.$(date +%Y%m%d_%H%M%S)"
        echo "✓ Current database backed up"
    fi
    
    # Restore database
    cp "$RESTORE_DIR/$BACKUP_NAME/trustgraph.db" /app/data/trustgraph.db
    echo "✓ Database restored"
fi

# Restore logs
if [ -f "$RESTORE_DIR/$BACKUP_NAME/logs.tar.gz" ]; then
    tar -xzf "$RESTORE_DIR/$BACKUP_NAME/logs.tar.gz" -C /app/
    echo "✓ Logs restored"
fi

# Cleanup
rm -rf "$RESTORE_DIR"
echo "✓ Cleanup completed"

echo ""
echo "=========================================="
echo "Restore completed successfully!"
echo "=========================================="
echo "Please restart the application for changes to take effect."
