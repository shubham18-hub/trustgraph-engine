#!/bin/bash
# TrustGraph Engine - Automated Backup Script
# Backs up database and critical data to S3

set -e

# Configuration
BACKUP_DIR="/tmp/trustgraph-backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="trustgraph-backup-${TIMESTAMP}"
S3_BUCKET="${S3_BACKUP_BUCKET:-trustgraph-backups-production}"
AWS_REGION="${AWS_REGION:-ap-south-1}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

echo "=========================================="
echo "TrustGraph Engine - Backup Script"
echo "=========================================="
echo "Timestamp: $TIMESTAMP"
echo "S3 Bucket: $S3_BUCKET"
echo "Region: $AWS_REGION"
echo "=========================================="

# Create backup directory
mkdir -p "$BACKUP_DIR/$BACKUP_NAME"

# Backup database
echo "[1/5] Backing up database..."
if [ -f "/app/data/trustgraph.db" ]; then
    cp /app/data/trustgraph.db "$BACKUP_DIR/$BACKUP_NAME/trustgraph.db"
    echo "✓ Database backed up"
else
    echo "⚠ Database file not found"
fi

# Backup logs
echo "[2/5] Backing up logs..."
if [ -d "/app/logs" ]; then
    tar -czf "$BACKUP_DIR/$BACKUP_NAME/logs.tar.gz" -C /app logs/
    echo "✓ Logs backed up"
else
    echo "⚠ Logs directory not found"
fi

# Backup configuration
echo "[3/5] Backing up configuration..."
if [ -f ".env.production" ]; then
    cp .env.production "$BACKUP_DIR/$BACKUP_NAME/.env.production"
    echo "✓ Configuration backed up"
fi

# Create backup metadata
echo "[4/5] Creating backup metadata..."
cat > "$BACKUP_DIR/$BACKUP_NAME/metadata.json" <<EOF
{
  "timestamp": "$TIMESTAMP",
  "backup_name": "$BACKUP_NAME",
  "environment": "production",
  "region": "$AWS_REGION",
  "version": "$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')",
  "hostname": "$(hostname)",
  "backup_size": "$(du -sh $BACKUP_DIR/$BACKUP_NAME | cut -f1)"
}
EOF
echo "✓ Metadata created"

# Compress backup
echo "[5/5] Compressing and uploading to S3..."
cd "$BACKUP_DIR"
tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"

# Upload to S3
aws s3 cp "${BACKUP_NAME}.tar.gz" "s3://${S3_BUCKET}/${BACKUP_NAME}.tar.gz" \
    --region "$AWS_REGION" \
    --storage-class STANDARD_IA \
    --server-side-encryption AES256

if [ $? -eq 0 ]; then
    echo "✓ Backup uploaded to S3"
    
    # Cleanup old backups
    echo "Cleaning up backups older than $RETENTION_DAYS days..."
    aws s3 ls "s3://${S3_BUCKET}/" --region "$AWS_REGION" | \
        awk '{print $4}' | \
        while read -r file; do
            file_date=$(echo "$file" | grep -oP '\d{8}' | head -1)
            if [ -n "$file_date" ]; then
                file_timestamp=$(date -d "$file_date" +%s)
                current_timestamp=$(date +%s)
                age_days=$(( (current_timestamp - file_timestamp) / 86400 ))
                
                if [ $age_days -gt $RETENTION_DAYS ]; then
                    echo "Deleting old backup: $file (${age_days} days old)"
                    aws s3 rm "s3://${S3_BUCKET}/${file}" --region "$AWS_REGION"
                fi
            fi
        done
else
    echo "✗ Failed to upload backup to S3"
    exit 1
fi

# Cleanup local backup
rm -rf "$BACKUP_DIR"
echo "✓ Local backup cleaned up"

echo ""
echo "=========================================="
echo "Backup completed successfully!"
echo "Backup location: s3://${S3_BUCKET}/${BACKUP_NAME}.tar.gz"
echo "=========================================="
