# https://www.rdocumentation.org/packages/base/versions/3.6.2/topics/file.choose
# https://rdrr.io/cran/urca/man/ur.za.html
library(readxl)
library(devtools)
library(urca)
## 會跳出視窗，讓你選擇檔案
mydata = read_excel(file.choose())

## Unit root test-zivot/Andrews with level data
# model = trend or intercept or both
z_both = ur.za(mydata$損失率,model='both')
z_intercept = ur.za(mydata$損失率,model='intercept')
summary(z_intercept)
summary(z_both)

# https://www.researchgate.net/post/How_can_I_interprete_a_Zivot-Andrews_1992_unit_root_test_given_structural_break_in_the_data

dz_intercept= ur.za(diff(mydata$損失率),model='intercept')
dz_both = ur.za(diff(mydata$損失率),model='both')
summary(dz_intercept)
summary(dz_both)
