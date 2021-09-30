# awsls
List AWS resources from multiple regions

# usage
## EC2
```
Usage: awsls ec2 [OPTIONS]

  List instances from AWS EC2

Options:
  -s, --state TEXT   running, stopped or terminated (default: return all states)
  -r, --region TEXT  AWS region (default: search all regions)
  -o, --output TEXT  output csv file (default: print on stdout)
  --help             Show this message and exit.
```
## S3
```
Usage: awsls s3 [OPTIONS]
  Return bucket size in Go

Options:
  -b, --bucket TEXT     name of the bucket (default: process all buckets)
  -H, --human-readable  print human readable units
  -s, --sort-by-size    sort by size
  --help                Show this message and exit.
```
