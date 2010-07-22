# should allow '20' to be passed in by user & default to BaseN
# (in which case topo's common_control._check_proj() would need adjusting)

define_param row_unit   Param_Integer   
define_param col_unit   Param_Integer   

### hack to get sstep=int(ceil(BaseN/20))
define_param sf Param_Float
define_param sstep Param_Integer
set sf=BaseN/20
set sstep=BaseN/20
if (sf>sstep) set sstep=sstep+1
###

# want an even sstep so that we get right&bottom borders
# (assuming even BaseN)
if (sstep>2) if (sstep%2==1) set sstep=sstep+1

echo "Saving plots for units in range(0,${BaseN},${sstep})"
for row_unit=0 row_unit<BaseN row_unit=row_unit+sstep exec \
"for col_unit=0 col_unit<BaseN col_unit=col_unit+sstep \
  plot_unit save_matrices=True row_unit col_unit"
