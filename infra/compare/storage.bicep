targetScope = 'resourceGroup'

@minLength(3)
@maxLength(24)
param storageAccountName string

@allowed(['sales', 'operations'])
param team string

@minLength(1)
param costCenter string

@minLength(1)
param owner string

param serviceLabel string = ''

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: 'italynorth'
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    publicNetworkAccess: 'Disabled'
    allowSharedKeyAccess: false
    allowBlobPublicAccess: false
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    defaultToOAuthAuthentication: true
  }
  tags: union({
    project: 'wpc-2026'
    environment: 'sandbox'
    tenant: team
    costCenter: costCenter
    owner: owner
  }, empty(serviceLabel) ? {} : {serviceLabel: serviceLabel})
}

output storageAccountId string = storage.id
