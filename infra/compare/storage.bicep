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
  tags: {
    project: 'wpc-2026'
    environment: 'sandbox'
    tenant: team
    costCenter: costCenter
    owner: owner
  }
}

output storageAccountId string = storage.id
