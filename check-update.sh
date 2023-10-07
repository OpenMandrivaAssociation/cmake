#!/bin/sh
curl https://cmake.org/download/ 2>/dev/null |grep 'Latest Release' |head -n1 |sed -e 's,.*(,,;s,).*,,' |sort -V |tail -n1
