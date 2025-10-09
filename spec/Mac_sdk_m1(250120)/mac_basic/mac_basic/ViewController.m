//
//  ViewController.m
//  mac_basic
//
//  Created by test on 18/1/16.
//  Copyright © 2018年 mv. All rights reserved.
//

#import "CameraApi.h"
#import "ViewController.h"
#import "sys/time.h"

@implementation ViewController

// ctrl
NSImageView* mImageView;
NSComboBox* mCamListCombo;
NSTextField* mExpEdit;
NSSlider* mExpSlider;
NSButton* mOpenButton;
NSButton* mCloseButton;
NSButton* mContinuousModeRadio;
NSButton* mTriggerModeRadio;
NSTextField* mStatLabel;

// roi ctrl
NSTextField* mRoiXEdit;
NSTextField* mRoiYEdit;
NSTextField* mRoiWEdit;
NSTextField* mRoiHEdit;

// camera
int mCameraHandle;
tSdkCameraDevInfo mCamList[16];
int mCamListSize;
tSdkCameraCapbility mCamCap;
BYTE* mFrameBuffer;

// thread
NSThread* mGrabThread;

// stat
NSTimer* mStatTimer;
struct timeval mLastStatTime;
int mLastCapCount;
int mLastDispCount;
int mTotalDispCount;
int mLastLostCount;
UINT mLastResendCount;
int mLastProcessImageWidth;
int mLastProcessImageHeight;


- (void)viewDidLoad {
    [super viewDidLoad];

    // Do any additional setup after loading the view.
    mImageView = (NSImageView*)[self viewWithIdentifier:@"prevImageView"];
    mCamListCombo = (NSComboBox*)[self viewWithIdentifier:@"camListCombo"];
    mExpEdit = (NSTextField*)[self viewWithIdentifier:@"exposureEdit"];
    mExpSlider = (NSSlider*)[self viewWithIdentifier:@"exposureSlider"];
    mOpenButton = (NSButton*)[self viewWithIdentifier:@"openButton"];
    mCloseButton = (NSButton*)[self viewWithIdentifier:@"closeButton"];
    mContinuousModeRadio = (NSButton*)[self viewWithIdentifier:@"continuousModeRadio"];
    mTriggerModeRadio = (NSButton*)[self viewWithIdentifier:@"triggerModeRadio"];
    mStatLabel = (NSTextField*)[self viewWithIdentifier:@"statLabel"];
    
    mRoiXEdit = (NSTextField*)[self viewWithIdentifier:@"roiXEdit"];
    mRoiYEdit = (NSTextField*)[self viewWithIdentifier:@"roiYEdit"];
    mRoiWEdit = (NSTextField*)[self viewWithIdentifier:@"roiWEdit"];
    mRoiHEdit = (NSTextField*)[self viewWithIdentifier:@"roiHEdit"];
    
    [mCloseButton setEnabled:FALSE];
    
    [self scanCamera];
}

- (void)viewWillAppear {
    mStatTimer = [NSTimer scheduledTimerWithTimeInterval:1.0 target:self selector:@selector(statTimerProc) userInfo:NULL repeats:TRUE];
}

- (void)viewWillDisappear {
    if (mStatTimer != NULL) {
        [mStatTimer invalidate];
        mStatTimer = nil;
    }
    [self closeCamera];
}

- (void)setRepresentedObject:(id)representedObject {
    [super setRepresentedObject:representedObject];

    // Update the view, if already loaded.
}

- (NSView*)viewWithIdentifier:(NSString*)identifier {
    for (NSView* view in [self.view subviews]) {
        if ([view.identifier isEqualToString:identifier]) {
            return view;
        }
    }
    return nil;
}

- (IBAction)scanClicked:(NSButton *)sender {
    [self scanCamera];
}

- (IBAction)openClicked:(NSButton *)sender {
    [self openCamera];
}

- (IBAction)closeClicked:(NSButton *)sender {
    [self closeCamera];
}

- (IBAction)expSliderAction:(NSSlider *)sender {
    if (mCameraHandle > 0) {
        double expLineTime;
        CameraGetExposureLineTime(mCameraHandle, &expLineTime);
        
        int expTime = mExpSlider.intValue * expLineTime;
        CameraSetExposureTime(mCameraHandle, expTime);
        
        mExpEdit.stringValue = [NSString stringWithFormat:@"%.3lf", expTime / 1000.0f];
    }
}

- (IBAction)expEditAction:(NSTextField *)sender {
    if (mCameraHandle > 0) {
        double expTime = mExpEdit.doubleValue * 1000.0f;
        CameraSetExposureTime(mCameraHandle, expTime);
        
        CameraGetExposureTime(mCameraHandle, &expTime);
        
        double expLineTime;
        CameraGetExposureLineTime(mCameraHandle, &expLineTime);
        mExpSlider.intValue = expTime / expLineTime;
        
        mExpEdit.stringValue = [NSString stringWithFormat:@"%.3lf", expTime / 1000.0f];
    }
}

- (IBAction)triggerModeAction:(NSButton *)sender {
    if (mCameraHandle > 0) {
        if (mContinuousModeRadio.state) {
            CameraSetTriggerMode(mCameraHandle, 0);
        }
        else {
            CameraSetTriggerMode(mCameraHandle, 1);
        }
        [self resetStat];
    }
}

- (IBAction)triggerClicked:(NSButton *)sender {
    if (mCameraHandle > 0) {
        CameraSoftTrigger(mCameraHandle);
    }
}

- (IBAction)roiApplyClicked:(NSButton *)sender {
    if (mCameraHandle > 0) {
        int x = mRoiXEdit.intValue;
        int y = mRoiYEdit.intValue;
        int w = mRoiWEdit.intValue;
        int h = mRoiHEdit.intValue;
        
        x = x / 16 * 16;
        y = y / 16 * 16;
        w = w / 16 * 16;
        h = h / 16 * 16;
        
        if (x >= 0 && y >= 0 && w > 0 && h > 0
            && (x + w) <= mCamCap.sResolutionRange.iWidthMax
            && (y + h) <= mCamCap.sResolutionRange.iHeightMax) {
            tSdkImageResolution res = { 0 };
            res.iIndex = 255;
            res.iHOffsetFOV = x;
            res.iVOffsetFOV = y;
            res.iWidth = res.iWidthFOV = w;
            res.iHeight = res.iHeightFOV = h;
            CameraSetImageResolution(mCameraHandle, &res);
            [self updateCameraResolutionUI];
        } else {
            NSAlert *alert = [[NSAlert alloc] init];
            [alert addButtonWithTitle:@"OK"];
            [alert setMessageText:@"Error"];
            [alert setInformativeText:@"Resolution value error!!"];
            [alert setAlertStyle:NSWarningAlertStyle];
            [alert runModal];
        }
    }
}

- (IBAction)roiMaxClicked:(NSButton *)sender {
    if (mCameraHandle > 0) {
        tSdkImageResolution res = { 0 };
        CameraSetImageResolution(mCameraHandle, &res);
        [self updateCameraResolutionUI];
    }
}

- (IBAction)wbOnceClicked:(NSButton *)sender {
    if (mCameraHandle > 0) {
        CameraSetOnceWB(mCameraHandle);
    }
}

- (IBAction)saveParamClicked:(NSButton *)sender {
    if (mCameraHandle > 0) {
        CameraSaveParameter(mCameraHandle, 0);
    }
}

- (void) scanCamera {
    [mCamListCombo removeAllItems];
    
    mCamListSize = sizeof(mCamList) / sizeof(mCamList[0]);
    CameraEnumerateDevice(mCamList, &mCamListSize);
    if (mCamListSize < 1)
        return;
    
    for (int i = 0; i < mCamListSize; ++i) {
        tSdkCameraDevInfo* info = &mCamList[i];
        [mCamListCombo addItemWithObjectValue: [[NSString alloc] initWithCString:info->acFriendlyName]];
    }
    [mCamListCombo selectItemAtIndex:0];
}

- (void) updateCameraResolutionUI {
    
    tSdkImageResolution res = { 0 };
    CameraGetImageResolution(mCameraHandle, &res);
    
    [mRoiXEdit setStringValue:[NSString stringWithFormat:@"%d", res.iHOffsetFOV]];
    [mRoiYEdit setStringValue:[NSString stringWithFormat:@"%d", res.iVOffsetFOV]];
    [mRoiWEdit setStringValue:[NSString stringWithFormat:@"%d", res.iWidth]];
    [mRoiHEdit setStringValue:[NSString stringWithFormat:@"%d", res.iHeight]];
}

- (void) updateCameraParamsUI {
    
    double expTime, expLineTime;
    CameraGetExposureTime(mCameraHandle, &expTime);
    CameraGetExposureLineTime(mCameraHandle, &expLineTime);
    
    mExpEdit.stringValue = [NSString stringWithFormat:@"%.3lf", expTime / 1000.0f];
    
    [mExpSlider setMinValue:mCamCap.sExposeDesc.uiExposeTimeMin];
    [mExpSlider setMaxValue:mCamCap.sExposeDesc.uiExposeTimeMax];
    mExpSlider.intValue = expTime / expLineTime;
    
    int triggerMode;
    CameraGetTriggerMode(mCameraHandle, &triggerMode);
    if (triggerMode == 0)
        [mContinuousModeRadio setState:1];
    else
        [mTriggerModeRadio setState:1];
    
    [self updateCameraResolutionUI];
}

- (Boolean)openCamera {
    
    int sel = (int)[mCamListCombo indexOfSelectedItem];
    if (sel < 0)
        return false;
    
    int err = CameraInit(&mCamList[sel], -1, -1, &mCameraHandle);
    if (err != CAMERA_STATUS_SUCCESS) {
        mCameraHandle = 0;
        
        NSAlert *alert = [[NSAlert alloc] init];
        [alert addButtonWithTitle:@"OK"];
        [alert setMessageText:@"Open failed"];
        [alert setInformativeText:[NSString stringWithFormat:@"open %s error: %d", mCamList[sel].acFriendlyName, err]];
        [alert setAlertStyle:NSWarningAlertStyle];
        [alert runModal];
        return false;
    }
    
    CameraGetCapability(mCameraHandle, &mCamCap);
    
    int FrameBufferSize = mCamCap.sResolutionRange.iWidthMax * mCamCap.sResolutionRange.iHeightMax;
    if (mCamCap.sIspCapacity.bMonoSensor)
    {
        CameraSetIspOutFormat(mCameraHandle, CAMERA_MEDIA_TYPE_MONO8);
    }
    else
    {
        FrameBufferSize *= 3;
        CameraSetIspOutFormat(mCameraHandle, CAMERA_MEDIA_TYPE_RGB8);
    }

    mFrameBuffer = CameraAlignMalloc(FrameBufferSize, 16);
    
    CameraSetAeState(mCameraHandle, FALSE);
    CameraSetExposureTime(mCameraHandle, 10 * 1000);
    CameraSetTriggerMode(mCameraHandle, 0);
    CameraPlay(mCameraHandle);
    
    [self resetStat];
    
    mGrabThread = [[NSThread alloc] initWithTarget:self selector:@selector(grabThreadProc) object:nil];
    [mGrabThread start];
    
    [mOpenButton setEnabled:FALSE];
    [mCloseButton setEnabled:TRUE];
    [self updateCameraParamsUI];
    return true;
}

- (void)closeCamera {
    if (mGrabThread != NULL) {
        [mGrabThread cancel];
        while (![mGrabThread isFinished]) {
            [[NSRunLoop mainRunLoop] runMode:NSDefaultRunLoopMode beforeDate: [NSDate distantFuture]];
        }
        mGrabThread = NULL;
    }
    
    if (mCameraHandle > 0) {
        CameraUnInit(mCameraHandle);
        mCameraHandle = 0;
    }
    
    if (mFrameBuffer != NULL) {
        CameraAlignFree(mFrameBuffer);
        mFrameBuffer = NULL;
    }
    
    [mOpenButton setEnabled:TRUE];
    [mCloseButton setEnabled:FALSE];
}

- (void)resetStat {
    mLastStatTime.tv_sec = 0;
    mLastStatTime.tv_usec = 0;
    mLastCapCount = 0;
    mLastDispCount = 0;
    mLastLostCount = 0;
    mLastResendCount = 0;
    mTotalDispCount = 0;
    mLastProcessImageWidth = 0;
    mLastProcessImageHeight = 0;
}

- (void)updateStat: (float*)pFpsDisp capFPS: (float*)pFpsCap {
    float fpsCap = 0, fpsDisp = 0;
    
    if (mCameraHandle > 0) {
        tSdkFrameStatistic stat;
        CameraGetFrameStatistic(mCameraHandle, &stat);
        
        int totalDispCount = mTotalDispCount;
        
        struct timeval curTime;
        gettimeofday(&curTime, NULL);
        
        bool bFirst = (mLastStatTime.tv_sec == 0 && mLastStatTime.tv_usec == 0);
        
        if (!bFirst) {
            float timeDiff = curTime.tv_sec - mLastStatTime.tv_sec + (curTime.tv_usec - mLastStatTime.tv_usec) / 1e6;
            fpsCap = (stat.iCapture - mLastCapCount) / timeDiff;
            fpsDisp = (totalDispCount - mLastDispCount) / timeDiff;
        }
        
        mLastCapCount = stat.iCapture;
        mLastDispCount = totalDispCount;
        mLastLostCount = stat.iLost;
        CameraGetStatisticResend(mCameraHandle, &mLastResendCount);
        mLastStatTime = curTime;
    }
    *pFpsDisp = fpsDisp;
    *pFpsCap = fpsCap;
}

- (void)statTimerProc {
    if (mCameraHandle > 0) {
        float fpsCap = 0, fpsDisp = 0;
        [self updateStat:&fpsDisp capFPS:&fpsCap];
        
        mStatLabel.stringValue = [NSString stringWithFormat:@"SIZE:%d*%d | DispFPS:%.2f | CapFPS:%.2f | Frames:%d | Lost:%d | Resend:%u", mLastProcessImageWidth, mLastProcessImageHeight, fpsDisp, fpsCap, mLastCapCount, mLastLostCount, mLastResendCount];
    } else {
        mStatLabel.stringValue = @"";
    }
}

- (void)updateImageView: (NSImage*)image {
    [mImageView setImage: image];
}

- (void)grabThreadProc {
    
    mTotalDispCount = 0;
    mLastProcessImageWidth = 0;
    mLastProcessImageHeight = 0;
    
    while (![[NSThread currentThread] isCancelled]) {
        NSImage* image = [self capImage: 200];
        if (image != nil) {
            [self performSelectorOnMainThread:@selector(updateImageView:) withObject:image waitUntilDone:TRUE];
            ++mTotalDispCount;
        }
    }
}

- (NSImage*)capImage: (int)timeout {
    tSdkFrameHead Head;
    BYTE* pRaw;
    
    int err = CameraGetImageBuffer(mCameraHandle, &Head, &pRaw, timeout);
    if (err != CAMERA_STATUS_SUCCESS) {
        return nil;
    }
    
    err = CameraImageProcess(mCameraHandle, pRaw, mFrameBuffer, &Head);
    CameraReleaseImageBuffer(mCameraHandle, pRaw);
    
    if (err != CAMERA_STATUS_SUCCESS)
    {
        NSLog(@"CameraImageProcess: %d", err);
        return nil;
    }
    
    mLastProcessImageWidth = Head.iWidth;
    mLastProcessImageHeight = Head.iHeight;
    
    return [self createImageFromBuffer: mFrameBuffer FrameHead: &Head];
}

static void BufferProviderReleaseData(void *info, const void *data, size_t size)
{
    free((void*)data);
}

- (NSImage*)createImageFromBuffer:(BYTE*)frameBuffer FrameHead:(tSdkFrameHead*)frameHead {
    
    int totalBytesForImage = frameHead->uBytes;
    void* frameBufferCopy = malloc(totalBytesForImage);
    if (frameBufferCopy != NULL) {
        memcpy(frameBufferCopy, frameBuffer, totalBytesForImage);
    } else {
        return nil;
    }
    
    CGDataProviderRef dataProvider = CGDataProviderCreateWithData(NULL, frameBufferCopy, totalBytesForImage, BufferProviderReleaseData);
    
    CGColorSpaceRef colorSpace;
    Boolean gray = frameHead->uiMediaType == CAMERA_MEDIA_TYPE_MONO8;
    if (gray)
        colorSpace = CGColorSpaceCreateDeviceGray();
    else
        colorSpace = CGColorSpaceCreateDeviceRGB();
    
    CGImageRef cgImageFromBytes = CGImageCreate(frameHead->iWidth,
                                                frameHead->iHeight,
                                                8,
                                                gray ? 8 : 24,
                                                gray ? frameHead->iWidth : 3 * frameHead->iWidth,
                                                colorSpace,
                                                kCGBitmapByteOrderDefault | (gray ? 0 : kCGImageAlphaNone),
                                                dataProvider, NULL, FALSE, kCGRenderingIntentDefault);
    
    CGDataProviderRelease(dataProvider);
    CGColorSpaceRelease(colorSpace);
    
    if (cgImageFromBytes == NULL)
        return nil;
    NSImage* image = createNSImageFromCGImageRef2(cgImageFromBytes);
    CGImageRelease(cgImageFromBytes);
    return image;
}

NSImage* createNSImageFromCGImageRef2(CGImageRef image)
{
    NSImage* newImage = nil;
    
    
#if MAC_OS_X_VERSION_MAX_ALLOWED >= MAC_OS_X_VERSION_10_5
    
    NSBitmapImageRep*newRep = [[NSBitmapImageRep alloc] initWithCGImage:image];
    
    NSSize imageSize;
    
    
    // Get the image dimensions.
    
    imageSize.height = CGImageGetHeight(image);
    
    imageSize.width = CGImageGetWidth(image);
    
    
    newImage = [[NSImage alloc] initWithSize:imageSize];
    
    [newImage addRepresentation:newRep];
    
    //[newRep release];
    
#else
    
    NSRect imageRect = NSMakeRect(0.0, 0.0, 0.0, 0.0);
    
    CGContextRef imageContext = nil;
    
    
    // Get the image dimensions.
    
    imageRect.size.height = CGImageGetHeight(image);
    
    imageRect.size.width = CGImageGetWidth(image);
    
    
    // Create a new image to receive the Quartz image data.
    
    newImage = [[NSImage alloc] initWithSize:imageRect.size];
    
    [newImage lockFocus];
    
    
    // Get the Quartz context and draw.
    
    imageContext = (CGContextRef)[[NSGraphicsContext currentContext] graphicsPort];
    
    CGContextDrawImage(imageContext, *(CGRect*)&imageRect, image);
    
    [newImage unlockFocus];
    
#endif
    
    return newImage;//[newImage autorelease];
}

- (void)saveImage:(NSImage *)image fileName:(NSString*)fname
{
    [image lockFocus];
    //先设置 下面一个实例
    NSBitmapImageRep *bits = [[NSBitmapImageRep alloc]initWithFocusedViewRect:NSMakeRect(0, 0, 640, 480)];
    [image unlockFocus];
    
    //再设置后面要用到得 props属性
    NSDictionary *imageProps = [NSDictionary dictionaryWithObject:[NSNumber numberWithFloat:0.9] forKey:NSImageCompressionFactor];
    
    
    //之后 转化为NSData 以便存到文件中
    NSData *imageData = [bits representationUsingType:NSJPEGFileType properties:imageProps];
    
    //设定好文件路径后进行存储就ok了
    [imageData writeToFile:fname atomically:TRUE];
}

@end
