variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones to use"
  type        = list(string)
}

variable "nat_gateway_count" {
  description = "Number of NAT gateways to create (1 for dev, 2 for prod HA)"
  type        = number
  default     = 1
}
