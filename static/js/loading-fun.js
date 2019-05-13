function loading1() {
	$('body').loading({
		loadingWidth:480,
		title:'请稍后',
		name:'install',
		discription:'正在安装数据库实例',
		direction:'column',
		type:'origin',
		// originBg:'#71EA71',
		originDivWidth:60,
		originDivHeight:60,
		originWidth:8,
		originHeight:8,
		smallLoading:false,
		loadingMaskBg:'rgba(0,0,0,0.2)'
	});
	$("p.loading-discription").css("font-size","18px");
}

function loading2() {
	$('body').loading({
		loadingWidth:240,
		title:'',
		name:'test',
		discription:'描述描述描述描述',
		direction:'column',
		type:'origin',
		// originBg:'#71EA71',
		originDivWidth:40,
		originDivHeight:40,
		originWidth:6,
		originHeight:6,
		smallLoading:false,
		loadingMaskBg:'rgba(0,0,0,0.2)'
	});

	setTimeout(function(){
		removeLoading('test');
	},3000);
}

function loading3() {
	$('body').loading({
		loadingWidth:120,
		title:'',
		name:'test',
		discription:'',
		direction:'column',
		type:'origin',
		// originBg:'#71EA71',
		originDivWidth:40,
		originDivHeight:40,
		originWidth:6,
		originHeight:6,
		smallLoading:false,
		loadingMaskBg:'rgba(0,0,0,0.2)'
	});

	setTimeout(function(){
		removeLoading('test');
	},3000);
}

function loading4() {
	$('body').loading({
		loadingWidth:240,
		title:'请稍等!',
		name:'test',
		discription:'这是一个描述...',
		direction:'column',
		type:'origin',
		originBg:'#71EA71',
		originDivWidth:40,
		originDivHeight:40,
		originWidth:6,
		originHeight:6,
		smallLoading:false,
		loadingBg:'#389A81',
		loadingMaskBg:'rgba(123,122,222,0.2)'
	});

	setTimeout(function(){
		removeLoading('test');
	},3000);
}

function loading5() {
	$('body').loading({
		loadingWidth:240,
		title:'请稍等!',
		name:'test',
		discription:'这是一个描述...',
		direction:'column',
		type:'pic',
		originBg:'#71EA71',
		originDivWidth:60,
		originDivHeight:60,
		originWidth:6,
		originHeight:6,
		smallLoading:false,
		loadingBg:'#389A81',
		loadingMaskBg:'rgba(123,122,222,0.2)'
	});

	setTimeout(function(){
		removeLoading('test');
	},3000);
}

function loading6() {
	$('body').loading({
		loadingWidth:240,
		title:'请稍等!',
		name:'test',
		discription:'这是一个描述...',
		direction:'row',
		type:'pic',
		originBg:'#71EA71',
		originDivWidth:60,
		originDivHeight:60,
		originWidth:6,
		originHeight:6,
		smallLoading:false,
		loadingBg:'rgba(20,125,148,0.8)',
		loadingMaskBg:'rgba(123,122,222,0.2)'
	});

	setTimeout(function(){
		removeLoading('test');
	},3000);
}

function loading7() {
	$('body').loading({
		loadingWidth:240,
		title:'请稍等!',
		name:'test',
		discription:'这是一个描述...',
		direction:'row',
		type:'origin',
		originBg:'#71EA71',
		originDivWidth:30,
		originDivHeight:30,
		originWidth:4,
		originHeight:4,
		smallLoading:false,
		titleColor:'#388E7A',
		loadingBg:'#312923',
		loadingMaskBg:'rgba(22,22,22,0.2)'
	});

	setTimeout(function(){
		removeLoading('test');
	},3000);
}

function loading8(){
	$('body').loading({
		loadingWidth:220,
		title:'提示',
		name:'test',
		titleColor:'#fff',
		discColor:'#EDEEE9',
		discription:'颜色搭配,我不太懂',
		direction:'column',
		type:'origin',
		originBg:'#ECCFBB',
		originDivWidth:40,
		originDivHeight:40,
		originWidth:6,
		originHeight:6,
		smallLoading:false,
		loadingBg:'rgba(56,43,14,0.8)',
		loadingMaskBg:'rgba(66,66,66,0.2)'
	});

	setTimeout(function(){
		removeLoading('test');
	},3000);
}

function loading10(){
	$('body').loading({
		loadingWidth:240,
		title:'请稍等!',
		name:'test',
		animateIn:'none',
		discription:'这是一个描述...',
		direction:'row',
		type:'origin',
		mustRelative:true,
		originBg:'#71EA71',
		originDivWidth:30,
		originDivHeight:30,
		originWidth:4,
		originHeight:4,
		smallLoading:false,
		titleColor:'#388E7A',
		loadingBg:'#312923',
		loadingMaskBg:'rgba(22,22,22,0.2)'
	});

	setTimeout(function(){
		removeLoading('test');
	},3000);
}
