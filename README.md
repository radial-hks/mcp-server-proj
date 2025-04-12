# mcp-server-proj MCP server

MCP Server PROJ (cartographic projections and coordinate transformations)

![](image/mcp_server_proj_transform.png)

### Tools

The server implements two coordinate transformation tools:

1. transform-coordinates
   - Transforms coordinates between different coordinate systems
   - Supports the following coordinate system formats:
     - EPSG codes (e.g., EPSG:4326 for WGS84)
     - WKT format
     - Proj format
   - Required input parameters:
     - source_crs: Source coordinate system
     - target_crs: Target coordinate system
     - coordinates: Array of points with x, y values
   
   Example: Transform from WGS84 (EPSG:4326) to Orthographic projection
   ```
   Input:
   - source_crs: EPSG:4326
   - target_crs: +proj=ortho +lon_0=112.364017384874 +lat_0=34.9227297291321 +a=6371010 +units=m +no_defs
   - coordinates: [112.364017384874, 34.9227297291321]
   
   Output:
   - transformed coordinates: [0.00000000, 0.00000000]
   ```

2. list-supported-crs
   - Lists all supported coordinate system formats with examples
   - Provides detailed examples for:
     - EPSG code format
     - WKT format for geographic and projected coordinate systems
     - Proj format

## Configuration

### Claude Desktop

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`
On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

<details>
  <summary>Development/Unpublished Servers Configuration</summary>

```json
{
  "mcpServers": {
    "mcp-server-proj": {
      "command": "uv",
      "args": [
        "--directory",
        "E:\\Code\\PythonDir\\MCP\\mcp-server-proj",
        "run",
        "mcp-server-proj"
      ]
    }
  }
}
```
</details>

<details>
  <summary>Published Servers Configuration</summary>

```json
{
  "mcpServers": {
    "mcp-server-proj": {
      "command": "uvx",
      "args": [
        "mcp-server-proj"
      ]
    }
  }
}
```
</details>

### Debugging

Since MCP servers run over stdio, debugging can be challenging. For the best debugging
experience, we strongly recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).

You can launch the MCP Inspector via [`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) with this command:

```bash
npx @modelcontextprotocol/inspector uv --directory E:\Code\PythonDir\MCP\mcp-server-proj run mcp-server-proj
```

Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.


## Coordinate System Information
### 1. EPSG (Coordinate System Unique Codes)
EPSG codes are unique identifiers for geographic and projected coordinate systems, commonly used in GIS software and programming libraries. Here are some common EPSG codes and their corresponding coordinate systems:
- EPSG:4326: WGS84 Geographic Coordinate System (GPS standard)
- EPSG:3857: Web Mercator Projection (used by Google Maps, AutoNavi Maps)

### 2. WKT (Well-Known Text Format)
WKT (Well-Known Text) is a human-readable coordinate system description format, widely used in GIS software and databases. Here are typical WKT structures:
- Geographic Coordinate System (GEOGCS)
```
GEOGCS["WGS 84",
  DATUM["WGS_1984",
    SPHEROID["WGS 84",6378137,298.257223563]],
  PRIMEM["Greenwich",0],
  UNIT["degree",0.0174532925199433]]
```
- Projected Coordinate System (PROJCS)
```
PROJCS["WGS 84 / UTM zone 50N",
  GEOGCS["WGS 84",...],
  PROJECTION["Transverse_Mercator"],
  PARAMETER["latitude_of_origin",0],
  PARAMETER["central_meridian",117],
  UNIT["metre",1]]
```
### 3. Proj (Concise Projection Parameter Expression)
Proj is a concise projection parameter expression format, commonly used in proj4 library and command-line tools. Here are typical Proj syntax examples:

WGS84:
```proj
+proj=longlat +datum=WGS84 +no_defs +type=crs
```

Web Mercator Projection:
```proj
+proj=merc +a=6378137 +b=6378137 +lat_ts=0 +lon_0=0 +x_0=0 +y_0=0 +k=1 +units=m +no_defs
```

## References
For more information about coordinate systems, visit: https://epsg.io/
If you're interested in JavaScript implementation of coordinate transformations, check out: https://github.com/proj4js/proj4js
